"""Auth endpoint tests — M0."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_creates_user_and_returns_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "supersecret"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "bob@example.com", "password": "supersecret"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 422
    assert second.json()["code"] == "email_taken"


@pytest.mark.asyncio
async def test_login_with_correct_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "supersecret"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "supersecret"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "password": "supersecret"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "supersecret"},
    )
    assert response.status_code == 401
