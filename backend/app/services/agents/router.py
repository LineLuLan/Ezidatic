"""Query router — classifies user questions to dispatch to a worker."""

import json
from enum import Enum

from app.config import settings
from app.services.agents.llm_adapter import LLMAdapter


class QueryType(str, Enum):
    SQL = "sql"
    ML = "ml"
    EDA = "eda"
    EXPLAIN = "explain"
    SMALL_TALK = "small_talk"


ROUTER_PROMPT = (
    'You are a router that classifies user questions about a dataset.\n'
    'Return JSON: {"type": "sql|ml|eda|explain|small_talk", "reason": "..."}\n\n'
    "Question: {question}"
)


async def route(question: str, llm: LLMAdapter) -> QueryType:
    """Use a lightweight model for cheap classification."""
    response = await llm.invoke(
        messages=[{"role": "user", "content": ROUTER_PROMPT.format(question=question)}],
        model_override=settings.groq_router_model,
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response)
    return QueryType(parsed["type"])
