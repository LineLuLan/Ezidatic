"""Chat endpoints — Sprint 4 (M5)."""

from fastapi import APIRouter

from app.schemas.chat import ChatMessageIn

router = APIRouter()


@router.post("/sessions")
async def create_session(_dataset_id: str | None = None) -> dict:
    raise NotImplementedError("Sprint 4 / M5_AGENTIC_CHAT: implement session create")


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, _payload: ChatMessageIn) -> dict:
    raise NotImplementedError("Sprint 4 / M5_AGENTIC_CHAT: implement send + SSE stream")
