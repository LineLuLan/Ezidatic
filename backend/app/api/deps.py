"""FastAPI dependencies — DB session + current user."""

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token


async def db_session() -> AsyncIterator[AsyncSession]:
    async for s in get_db():
        yield s


async def current_user_id(
    authorization: str | None = Header(default=None),
) -> UUID:
    """Extract user UUID from `Authorization: Bearer <jwt>`."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("Invalid token")
    return UUID(payload["sub"])


CurrentUserDep = Depends(current_user_id)
DbDep = Depends(db_session)
