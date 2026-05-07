"""Chat endpoints — Sprint 4 (M5)."""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.core.exceptions import AllProvidersFailedError, NotFoundError, ValidationError
from app.models.chat import ChatMessage, ChatSession
from app.models.dataset import Dataset
from app.models.workspace import Workspace
from app.schemas.chat import (
    ChatMessageIn,
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionOut,
)
from app.services.agents.llm_adapter import LLMAdapter
from app.services.agents.router import QueryType, route
from app.services.agents.workers.explain_worker import (
    build_grounded_context,
    explain_worker,
)
from app.services.agents.workers.sql_worker import sql_worker_stream

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/sessions", response_model=ChatSessionOut)
async def create_session(
    payload: ChatSessionCreate,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> ChatSessionOut:
    if payload.dataset_id is not None:
        dataset = await db.get(Dataset, payload.dataset_id)
        if dataset is None or dataset.workspace_id != workspace.id:
            raise NotFoundError("Dataset not found")

    session = ChatSession(
        workspace_id=workspace.id,
        dataset_id=payload.dataset_id,
        title=payload.title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ChatSessionOut.model_validate(session)


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[ChatSessionOut]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.workspace_id == workspace.id)
        .order_by(ChatSession.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [ChatSessionOut.model_validate(r) for r in rows]


@router.get(
    "/sessions/{session_id}/messages", response_model=list[ChatMessageOut]
)
async def list_messages(
    session_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[ChatMessageOut]:
    session = await db.get(ChatSession, session_id)
    if session is None or session.workspace_id != workspace.id:
        raise NotFoundError("Session not found")

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [ChatMessageOut.model_validate(r) for r in rows]


def _sse_event(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, default=str)}\n\n"


async def _generate_response(
    session: ChatSession,
    payload: ChatMessageIn,
    db: AsyncSession,
) -> AsyncIterator[dict[str, Any]]:
    """Yield SSE-friendly events. The endpoint serialises them as
    `data: ...\\n\\n`. Final event type is ``done`` with full content +
    metadata; the caller persists the assistant ChatMessage from there.
    """
    dataset_id = payload.dataset_id or session.dataset_id
    llm = LLMAdapter()
    full_text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    try:
        intent = await route(payload.content, llm)
    except AllProvidersFailedError as e:
        yield {"type": "error", "message": str(e)}
        return
    yield {"type": "intent", "value": intent.value}

    try:
        if intent == QueryType.SQL and dataset_id is not None:
            async for ev in sql_worker_stream(
                payload.content, dataset_id, db, llm
            ):
                if ev["type"] == "delta":
                    full_text_parts.append(ev["text"])
                    yield ev
                elif ev["type"] == "tool_calls":
                    tool_calls.extend(ev["data"])
        elif intent == QueryType.SQL and dataset_id is None:
            yield {
                "type": "delta",
                "text": "Attach a dataset to this session to run SQL.",
            }
            full_text_parts.append("Attach a dataset to this session to run SQL.")
        else:
            # explain / eda / ml / small_talk → stream a contextual reply.
            # Q5-AGENT-04: ground the prompt in real per-column stats so the
            # LLM can cite actual values instead of inventing them.
            ctx = ""
            if dataset_id is not None:
                dataset = await db.get(Dataset, dataset_id)
                if dataset is not None and dataset.profile is not None:
                    ctx = build_grounded_context(
                        question=payload.content,
                        profile=dataset.profile,
                        dataset_name=dataset.original_name or "",
                    )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a data analyst assistant for the Ezidatic "
                        "platform. Be concise. If the user asks for charts "
                        "or model training, point them at the EDA / AutoML "
                        "pages instead of trying to render here."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Context:\n{ctx}\n\nUser message: {payload.content}"
                        if ctx
                        else payload.content
                    ),
                },
            ]
            async for chunk in llm.stream(
                messages, temperature=0.4, max_tokens=600
            ):
                full_text_parts.append(chunk)
                yield {"type": "delta", "text": chunk}
    except AllProvidersFailedError as e:
        yield {"type": "error", "message": str(e)}
        return
    except Exception as e:  # noqa: BLE001
        log.exception("chat dispatch failed")
        yield {"type": "error", "message": f"{type(e).__name__}: {e}"}
        return

    yield {
        "type": "done",
        "content": "".join(full_text_parts),
        "tool_calls": tool_calls,
        "provider_used": llm.last_provider,
        "token_usage": llm.last_usage,
        "intent": intent.value,
    }


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    payload: ChatMessageIn,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> StreamingResponse:
    if not payload.content.strip():
        raise ValidationError("Empty message")

    session = await db.get(ChatSession, session_id)
    if session is None or session.workspace_id != workspace.id:
        raise NotFoundError("Session not found")

    # Persist the user message before streaming starts.
    user_row = ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.content,
    )
    db.add(user_row)
    await db.commit()

    async def event_stream() -> AsyncIterator[str]:
        final: dict[str, Any] | None = None
        async for event in _generate_response(session, payload, db):
            yield _sse_event(event)
            if event.get("type") == "done":
                final = event
        if final is None:
            return
        # Persist the assistant turn after streaming finishes.
        db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=final.get("content") or "",
                tool_calls=final.get("tool_calls") or None,
                token_usage=final.get("token_usage") or None,
                provider_used=final.get("provider_used"),
            )
        )
        await db.commit()
        yield _sse_event({"type": "saved"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
