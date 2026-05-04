"""sql_worker — generate Polars-SQL via LLM, execute, summarise.

Flow:
  1. Build a column-schema description for the prompt.
  2. Ask the LLM (one-shot, low temp) for a SELECT statement.
  3. Execute via the query_dataset tool.
  4. Stream the final natural-language summary back to the caller.

The session endpoint (api/v1/chat.py) consumes the AsyncIterator yielded
by ``sql_worker_stream`` and forwards each chunk as an SSE token. The
tool call info is attached to the assistant ChatMessage's
``tool_calls`` JSON column.
"""

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.services.agents.llm_adapter import LLMAdapter
from app.services.agents.tools import ToolRegistry

log = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:sql)?\s*(.+?)```", re.IGNORECASE | re.DOTALL)


def _extract_sql(raw: str) -> str:
    m = _FENCE_RE.search(raw)
    if m:
        return m.group(1).strip()
    # Strip leading "SQL:" labels and any prose.
    cleaned = raw.strip()
    if cleaned.lower().startswith("sql:"):
        cleaned = cleaned[4:].strip()
    return cleaned


async def _column_schema(dataset: Dataset) -> str:
    profile = dataset.profile or {}
    cols = profile.get("columns", [])
    return ", ".join(f"{c['name']} ({c['dtype']})" for c in cols) or "(unknown)"


async def sql_worker_stream(
    question: str,
    dataset_id: UUID,
    db: AsyncSession,
    llm: LLMAdapter,
) -> AsyncIterator[dict[str, Any]]:
    """Yield events: {"type": "tool_call", "data": {...}} and
    {"type": "delta", "text": "..."} (multiple). Final
    {"type": "tool_calls", "data": [...]} captures the full audit so
    the caller can persist on the assistant message row.
    """
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None:
        yield {"type": "delta", "text": f"Dataset {dataset_id} not found."}
        return

    schema = await _column_schema(dataset)
    sql_prompt = (
        "You are a Polars SQL generator. The dataset is exposed as the table "
        f"'data' with columns: {schema}.\n"
        "Reply with ONE SQL SELECT statement. No prose, no markdown fences, "
        "no comments. Use only ANSI SQL Polars supports (SELECT, WHERE, "
        "GROUP BY, ORDER BY, LIMIT, basic aggregates).\n\n"
        f"User question: {question}"
    )
    sql_resp = await llm.invoke(
        messages=[{"role": "user", "content": sql_prompt}],
        temperature=0.0,
        max_tokens=200,
    )
    sql = _extract_sql(sql_resp.content)

    tool = ToolRegistry.get("query_dataset")
    tool_call: dict[str, Any] = {
        "name": "query_dataset",
        "args": {"sql": sql},
        "provider": sql_resp.provider,
    }
    try:
        tool_result = await tool.execute(sql=sql, dataset_id=dataset_id, db=db)
        tool_call["result"] = {
            "columns": tool_result["columns"],
            "row_count": tool_result["row_count"],
            "preview_rows": tool_result["rows"][:5],
            "truncated": tool_result["truncated"],
        }
    except Exception as e:  # noqa: BLE001
        tool_call["error"] = str(e)
        yield {
            "type": "delta",
            "text": f"I tried this SQL:\n\n```sql\n{sql}\n```\n\nbut it failed: {e}",
        }
        yield {"type": "tool_calls", "data": [tool_call]}
        return

    summary_messages = [
        {
            "role": "system",
            "content": (
                "You are a data analyst. Summarise the SQL query result for "
                "the user. Cite the SQL exactly once in a code block."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SQL run: {sql}\n\n"
                f"Result columns: {tool_result['columns']}\n"
                f"Total rows: {tool_result['row_count']}\n"
                f"Preview ({min(5, len(tool_result['rows']))} rows):\n"
                f"{json.dumps(tool_result['rows'][:5], default=str)}"
            ),
        },
    ]
    async for chunk in llm.stream(summary_messages, temperature=0.3, max_tokens=400):
        yield {"type": "delta", "text": chunk}
    yield {"type": "tool_calls", "data": [tool_call]}
