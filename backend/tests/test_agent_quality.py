"""Sprint 5 P0 agent quality tests — Q5-AGENT-01 + Q5-AGENT-02.

These exercise the prompt-engineering layer (router few-shot block and
SQL worker schema enrichment) in isolation. The live-model acceptance
criteria from `docs/modules/M_QUALITY.md` (≥80% / ≥8 of 10 first-try
SQL) require real LLM calls and are not run in CI; the deterministic
checks here cover prompt construction + caching of profile fields.
"""

from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.services.agents.router import ROUTER_PROMPT
from app.services.agents.workers.sql_worker import (
    _SCHEMA_CHAR_BUDGET,
    _column_schema,
)
from app.services.eda.profiler import profile_dataframe

import polars as pl


# ---------------------------------------------------------------------------
# Q5-AGENT-01 — Router few-shot examples
# ---------------------------------------------------------------------------


def test_router_prompt_carries_examples_for_every_category() -> None:
    """The few-shot block must include an example for each QueryType."""
    rendered = ROUTER_PROMPT.format(question="placeholder")
    assert "Examples:" in rendered
    # Every category appears at least once inside an A: line.
    for label in ("sql", "ml", "eda", "explain", "small_talk"):
        assert f'"type": "{label}"' in rendered, f"missing example for {label}"


def test_router_prompt_has_three_examples_per_category() -> None:
    """3-5 labeled examples per category per Q5-AGENT-01 acceptance."""
    rendered = ROUTER_PROMPT.format(question="placeholder")
    for label in ("sql", "ml", "eda", "explain", "small_talk"):
        count = rendered.count(f'"type": "{label}"')
        assert count >= 3, f"expected ≥3 examples for {label}, got {count}"


def test_router_prompt_keeps_question_placeholder() -> None:
    """Format string must still substitute {question}."""
    rendered = ROUTER_PROMPT.format(question="how many rows?")
    assert "Question: how many rows?" in rendered
    assert "{question}" not in rendered  # placeholder fully replaced


# ---------------------------------------------------------------------------
# Q5-AGENT-02 — SQL worker schema enrichment
# ---------------------------------------------------------------------------


def _fake_dataset(profile: dict[str, Any]) -> Any:
    """Lightweight Dataset stand-in — _column_schema only reads .profile."""
    return SimpleNamespace(id=uuid4(), profile=profile)


@pytest.fixture
def sample_profile() -> dict[str, Any]:
    df = pl.DataFrame(
        {
            "age": [30, 25, 40, 35, 28, 50],
            "salary": [50000, 45000, 80000, 72000, 48000, 120000],
            "city": ["Hanoi", "Saigon", "Hanoi", "Saigon", "Danang", "Hanoi"],
        }
    )
    return profile_dataframe(df)


@pytest.mark.asyncio
async def test_column_schema_includes_stats_and_samples(
    sample_profile,
) -> None:
    """Schema string must contain min/max for numerics and samples for cats."""
    rendered = await _column_schema(_fake_dataset(sample_profile))
    # Numeric stats present
    assert "min=" in rendered
    assert "max=" in rendered
    # Categorical column with samples
    assert "city" in rendered
    assert "samples=[" in rendered
    # Each line is one column (one - prefix per column)
    assert rendered.count("\n- ") == 2  # 3 cols → 2 inter-line breaks


@pytest.mark.asyncio
async def test_column_schema_carries_unique_and_null_counts(
    sample_profile,
) -> None:
    rendered = await _column_schema(_fake_dataset(sample_profile))
    assert "nulls=" in rendered
    assert "unique=" in rendered
    # Spot-check: city has 3 unique values across 6 rows.
    assert "unique=3" in rendered


@pytest.mark.asyncio
async def test_column_schema_truncates_when_over_budget() -> None:
    """Many-column dataset gets truncated with an omission marker."""
    # Build a profile with 200 numeric columns so the rendered output
    # blows past the default 1500-char budget.
    cols = []
    for i in range(200):
        cols.append(
            {
                "name": f"col_{i}",
                "dtype": "Int64",
                "null_count": 0,
                "unique_count": 5,
                "sample_values": ["1", "2", "3"],
                "stats": {"min": 0.0, "max": 10.0, "mean": 5.0, "std": 2.0},
            }
        )
    profile = {"row_count": 100, "column_count": 200, "columns": cols}
    rendered = await _column_schema(_fake_dataset(profile))
    assert len(rendered) <= _SCHEMA_CHAR_BUDGET
    assert "more columns omitted" in rendered


@pytest.mark.asyncio
async def test_column_schema_handles_missing_profile() -> None:
    """Backwards-compat: dataset without a profile returns (unknown)."""
    assert await _column_schema(_fake_dataset({})) == "(unknown)"
    assert await _column_schema(_fake_dataset(None)) == "(unknown)"


# ---------------------------------------------------------------------------
# Q5-AGENT-02 — profiler emits sample_values
# ---------------------------------------------------------------------------


def test_profile_column_includes_sample_values() -> None:
    df = pl.DataFrame(
        {
            "country": ["VN", "US", "JP", "VN", "US", "VN"],
            "score": [1, 2, 3, 4, 5, 6],
        }
    )
    profile = profile_dataframe(df)
    cols = {c["name"]: c for c in profile["columns"]}
    assert "sample_values" in cols["country"]
    assert "sample_values" in cols["score"]
    assert len(cols["country"]["sample_values"]) == 3
    assert len(cols["score"]["sample_values"]) == 3
    # Values render as strings (so the SQL prompt can quote them safely).
    assert all(isinstance(v, str) for v in cols["country"]["sample_values"])


# ---------------------------------------------------------------------------
# Q5-AGENT-04 — Explain worker grounded context
# ---------------------------------------------------------------------------


from app.services.agents.workers.explain_worker import build_grounded_context


def test_grounded_context_carries_real_stats() -> None:
    df = pl.DataFrame(
        {
            "salary": [50000, 60000, 70000, 80000, 90000],
            "city": ["Hanoi", "Saigon", "Hanoi", "Danang", "Hanoi"],
        }
    )
    profile = profile_dataframe(df)

    text = build_grounded_context(
        question="what is the average salary?",
        profile=profile,
        dataset_name="payroll",
    )
    assert "Dataset: payroll" in text
    assert "5 rows" in text
    assert "salary" in text
    # 50k..90k mean = 70k → rendered as integer "70000".
    assert "mean=70000" in text
    assert "city" in text
    assert "Hanoi" in text


def test_grounded_context_prioritises_keyword_matches() -> None:
    """Columns whose name overlaps with the question land in top-N first."""
    cols = [
        {
            "name": f"unrelated_{i}",
            "dtype": "Int64",
            "null_count": 0,
            "unique_count": 5,
            "sample_values": [],
            "stats": {"mean": 1.0, "min": 0.0, "max": 2.0, "std": 0.5},
        }
        for i in range(15)
    ]
    cols.append(
        {
            "name": "salary",
            "dtype": "Float64",
            "null_count": 0,
            "unique_count": 5,
            "sample_values": ["100", "200", "300"],
            "stats": {
                "mean": 75000.0,
                "min": 50000.0,
                "max": 100000.0,
                "std": 1000.0,
            },
        }
    )
    profile = {"row_count": 5, "column_count": 16, "columns": cols}

    text = build_grounded_context(
        question="explain the salary distribution",
        profile=profile,
        max_columns=3,
    )
    assert "salary" in text
    rendered = sum(1 for line in text.splitlines() if line.startswith("- "))
    assert rendered == 3


def test_grounded_context_handles_empty_or_none_profile() -> None:
    assert build_grounded_context("q", None) == ""
    assert build_grounded_context("q", {}) == ""
    assert build_grounded_context("q", {"columns": []}) == ""


def test_grounded_context_truncates_to_budget() -> None:
    cols = [
        {
            "name": f"col_{i}",
            "dtype": "Int64",
            "null_count": 0,
            "unique_count": 5,
            "sample_values": ["1", "2", "3"],
            "stats": {"mean": 5.0, "min": 0.0, "max": 10.0, "std": 1.0},
        }
        for i in range(200)
    ]
    profile = {"row_count": 100, "column_count": 200, "columns": cols}

    text = build_grounded_context("anything", profile, max_chars=400)
    assert len(text) <= 400
    assert text.endswith("...")
