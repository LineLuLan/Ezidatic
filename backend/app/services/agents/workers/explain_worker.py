"""Explain worker — answers free-form 'why/what' questions about data or models.

Sample stub for Sprint 4 (M5_AGENTIC_CHAT). Implementations of sql_worker /
ml_worker follow the same shape.

Q5-AGENT-04 added ``build_grounded_context`` so the chat endpoint's EXPLAIN
branch can hand the LLM real per-column stats (mean / min / max / samples)
instead of just column names. That lets the model cite actual computed
values like "average salary is 65000" instead of inventing one.
"""

import re
from typing import Any

from app.services.agents.llm_adapter import LLMAdapter


_EXPLAIN_CONTEXT_MAX_CHARS = 1500
_EXPLAIN_CONTEXT_MAX_COLUMNS = 10


def _format_number(v: float) -> str:
    if v == int(v):
        return str(int(v))
    return f"{v:.4g}"


def _question_tokens(question: str) -> set[str]:
    """Lowercase word tokens >=2 chars from the question, for keyword overlap."""
    return set(re.findall(r"\w{2,}", question.lower()))


def _column_keyword_score(col: dict[str, Any], tokens: set[str]) -> int:
    """Score = number of question tokens that appear in the column name."""
    name_tokens = set(re.findall(r"\w{2,}", col.get("name", "").lower()))
    return len(name_tokens & tokens)


def build_grounded_context(
    question: str,
    profile: dict[str, Any] | None,
    dataset_name: str = "",
    max_columns: int = _EXPLAIN_CONTEXT_MAX_COLUMNS,
    max_chars: int = _EXPLAIN_CONTEXT_MAX_CHARS,
) -> str:
    """Build a profile snippet for the EXPLAIN branch.

    Q5-AGENT-04: prioritises columns whose names overlap with the
    question's tokens (so "average salary?" pulls the salary column to
    the top), then numeric columns, then everything else. Each
    selected column emits one line with dtype + nulls + unique +
    mean/min/max/std (if numeric) + up to 3 sample values. Capped at
    ``max_chars`` to keep free-tier provider context budgets safe.
    """
    if not profile:
        return ""
    cols = profile.get("columns", []) or []
    if not cols:
        return ""

    tokens = _question_tokens(question)

    def sort_key(col: dict[str, Any]) -> tuple[int, int, str]:
        return (
            -_column_keyword_score(col, tokens),
            0 if col.get("stats") else 1,
            str(col.get("name", "")),
        )

    ranked = sorted(cols, key=sort_key)
    selected = ranked[:max_columns]

    lines: list[str] = []
    if dataset_name:
        lines.append(f"Dataset: {dataset_name}")
    row_count = profile.get("row_count")
    column_count = profile.get("column_count")
    if row_count is not None and column_count is not None:
        lines.append(f"Shape: {row_count} rows x {column_count} columns")
    shown = min(max_columns, len(cols))
    lines.append(f"Top {shown} columns most relevant to the question:")

    for col in selected:
        parts = [f"- {col['name']} ({col['dtype']})"]
        parts.append(f"nulls={col.get('null_count', 0)}")
        parts.append(f"unique={col.get('unique_count', 0)}")
        stats = col.get("stats")
        if stats:
            parts.append(f"mean={_format_number(stats['mean'])}")
            parts.append(f"min={_format_number(stats['min'])}")
            parts.append(f"max={_format_number(stats['max'])}")
            parts.append(f"std={_format_number(stats['std'])}")
        samples = col.get("sample_values") or []
        if samples:
            parts.append(f"samples=[{', '.join(repr(s) for s in samples[:3])}]")
        lines.append(" | ".join(parts))

    text = "\n".join(lines)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


async def explain_worker(question: str, context: str, llm: LLMAdapter) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a data analyst. Explain clearly using the provided context. "
                "If the context is insufficient, say so."
            ),
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    return (await llm.invoke(messages)).content
