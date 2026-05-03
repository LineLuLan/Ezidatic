"""FastAPI dependencies — DB session + current user/workspace."""

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.models.user import User
from app.models.workspace import Workspace


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


async def current_user(
    user_id: UUID = Depends(current_user_id),
    db: AsyncSession = Depends(db_session),
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("User no longer exists")
    return user


async def current_workspace(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(db_session),
) -> Workspace:
    """Return the user's primary workspace (oldest one they own)."""
    stmt = (
        select(Workspace)
        .where(Workspace.owner_id == user.id)
        .order_by(Workspace.created_at)
        .limit(1)
    )
    workspace = (await db.execute(stmt)).scalar_one_or_none()
    if workspace is None:
        raise NotFoundError("No workspace for user")
    return workspace
