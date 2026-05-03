"""Auth endpoints — Sprint 1 (M0)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


def _issue_token(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(db_session),
) -> TokenResponse:
    """Create a User + personal Workspace, return an access token."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise ValidationError("Email already registered", code="email_taken")

    user = User(email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()  # populate user.id before referencing it

    workspace = Workspace(owner_id=user.id, name=f"{payload.email}'s workspace")
    db.add(workspace)
    await db.commit()
    await db.refresh(user)
    return _issue_token(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(db_session),
) -> TokenResponse:
    """Verify password and return an access token."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not user.password_hash:
        raise UnauthorizedError("Invalid email or password")
    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    return _issue_token(user)
