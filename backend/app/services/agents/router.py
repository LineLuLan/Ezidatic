"""Query router — classifies user questions to dispatch to a worker."""

import json
import logging
import re
from enum import Enum

from app.config import settings
from app.services.agents.llm_adapter import LLMAdapter

log = logging.getLogger(__name__)


class QueryType(str, Enum):
    SQL = "sql"
    ML = "ml"
    EDA = "eda"
    EXPLAIN = "explain"
    SMALL_TALK = "small_talk"


ROUTER_PROMPT = (
    'You are a router that classifies user questions about a dataset into one '
    'of: sql (data filtering/aggregation), ml (model training/prediction), '
    'eda (charts/profiles/distributions), explain (why/what reasoning), '
    'small_talk (greetings/meta).\n'
    'Reply with ONLY a single JSON object on one line, no prose, no code '
    'fences. Schema: {{"type": "...", "reason": "..."}}\n\n'
    'Examples:\n'
    'Q: "how many rows have salary > 50000?"\n'
    'A: {{"type": "sql", "reason": "filter+count"}}\n'
    'Q: "average age by department"\n'
    'A: {{"type": "sql", "reason": "group aggregate"}}\n'
    'Q: "top 10 oldest customers"\n'
    'A: {{"type": "sql", "reason": "order+limit"}}\n'
    'Q: "train a classifier to predict churn"\n'
    'A: {{"type": "ml", "reason": "supervised training"}}\n'
    'Q: "which model fits this dataset best?"\n'
    'A: {{"type": "ml", "reason": "model selection"}}\n'
    'Q: "predict next month revenue"\n'
    'A: {{"type": "ml", "reason": "regression forecast"}}\n'
    'Q: "show the distribution of age"\n'
    'A: {{"type": "eda", "reason": "histogram"}}\n'
    'Q: "is there correlation between salary and tenure?"\n'
    'A: {{"type": "eda", "reason": "correlation chart"}}\n'
    'Q: "give me a profile of the city column"\n'
    'A: {{"type": "eda", "reason": "column profile"}}\n'
    'Q: "why is salary high in engineering?"\n'
    'A: {{"type": "explain", "reason": "causal reasoning"}}\n'
    'Q: "what does this dataset describe?"\n'
    'A: {{"type": "explain", "reason": "dataset summary"}}\n'
    'Q: "summarise the trends you see"\n'
    'A: {{"type": "explain", "reason": "narrative summary"}}\n'
    'Q: "hi"\n'
    'A: {{"type": "small_talk", "reason": "greeting"}}\n'
    'Q: "thanks!"\n'
    'A: {{"type": "small_talk", "reason": "social"}}\n'
    'Q: "what can you do?"\n'
    'A: {{"type": "small_talk", "reason": "meta capability"}}\n'
    '\n'
    'Question: {question}'
)


_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\"type\"[^{}]*\}", re.DOTALL)


def _parse_router_json(raw: str) -> dict | None:
    """Extract a router-shaped JSON dict from raw LLM output.

    Tolerates markdown code fences, leading/trailing prose, and whitespace.
    Returns None if no salvageable JSON object is found.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK_RE.search(raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


async def route(question: str, llm: LLMAdapter) -> QueryType:
    """Use a lightweight model for cheap classification.

    Robust to non-Groq providers that don't honour
    ``response_format=json_object``. Falls back to ``EXPLAIN`` if the
    output cannot be parsed — explain_worker is the safest catch-all
    handler since it doesn't require structured tool output.
    """
    response = await llm.invoke(
        messages=[
            {"role": "user", "content": ROUTER_PROMPT.format(question=question)}
        ],
        model_override=settings.groq_router_model,
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=120,
    )

    parsed = _parse_router_json(response.content)
    if not parsed or "type" not in parsed:
        log.warning(
            "router could not parse output (provider=%s): %r",
            response.provider,
            response.content[:200],
        )
        return QueryType.EXPLAIN
    try:
        return QueryType(parsed["type"])
    except ValueError:
        log.warning("router emitted unknown type %r; defaulting to EXPLAIN", parsed["type"])
        return QueryType.EXPLAIN
