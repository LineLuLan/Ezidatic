"""Auth endpoints — Sprint 1 (M0)."""

from fastapi import APIRouter, status

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(_payload: RegisterRequest) -> TokenResponse:
    raise NotImplementedError("Sprint 1 / M0_AUTH: implement register")


@router.post("/login", response_model=TokenResponse)
async def login(_payload: LoginRequest) -> TokenResponse:
    raise NotImplementedError("Sprint 1 / M0_AUTH: implement login")
