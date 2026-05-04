"""Explain worker — answers free-form 'why/what' questions about data or models.

Sample stub for Sprint 4 (M5_AGENTIC_CHAT). Implementations of sql_worker /
ml_worker follow the same shape.
"""

from app.services.agents.llm_adapter import LLMAdapter


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
