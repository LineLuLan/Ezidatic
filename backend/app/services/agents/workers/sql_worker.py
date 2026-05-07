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


_SCHEMA_CHAR_BUDGET = 1500


def _format_number(v: float) -> str:
    """Render a float without trailing zeros for compact prompts."""
    if v == int(v):
        return str(int(v))
    return f"{v:.4g}"


def _format_column_line(col: dict[str, Any]) -> str:
    parts = [f"- {col['name']} ({col['dtype']})"]
    parts.append(f"nulls={col.get('null_count', 0)}")
    parts.append(f"unique={col.get('unique_count', 0)}")
    stats = col.get("stats")
    if stats:
        parts.append(f"min={_format_number(stats['min'])}")
        parts.append(f"max={_format_number(stats['max'])}")
    samples = col.get("sample_values") or []
    if samples:
        rendered = ", ".join(repr(s) for s in samples[:3])
        parts.append(f"samples=[{rendered}]")
    return " | ".join(parts)


async def _column_schema(
    dataset: Dataset, max_chars: int = _SCHEMA_CHAR_BUDGET
) -> str:
    """Render a richer column schema for the SQL worker prompt.

    Q5-AGENT-02: instead of just `name (dtype)`, expose null/unique
    counts, numeric min/max, and up to 3 sample values per column.
    Capped at ``max_chars`` so free-tier provider context budgets stay
    safe; remaining columns are summarised as a count.
    """
    profile = dataset.profile or {}
    cols = profile.get("columns", [])
    if not cols:
        return "(unknown)"

    lines = [_format_column_line(c) for c in cols]
    schema = "\n".join(lines)
    if len(schema) <= max_chars:
        return schema

    out: list[str] = []
    used = 0
    for i, line in enumerate(lines):
        if used + len(line) + 1 > max_chars:
            remaining = len(lines) - i
            out.append(f"- ... ({remaining} more columns omitted to fit context)")
            break
        out.append(line)
        used += len(line) + 1
    return "\n".join(out)


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
        "'data'. Columns (one per line, with nulls/unique/min/max/samples):\n"
        f"{schema}\n\n"
        "Use the sample values to spell categorical filters correctly "
        "(case-sensitive). Use min/max to keep numeric thresholds in "
        "range. Reply with ONE SQL SELECT statement. No prose, no "
        "markdown fences, no comments. Use only ANSI SQL Polars supports "
        "(SELECT, WHERE, GROUP BY, ORDER BY, LIMIT, basic aggregates).\n\n"
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
