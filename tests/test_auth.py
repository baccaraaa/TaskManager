import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    user_data = {"email": "dup@example.com", "username": "user1", "password": "password123"}
    await client.post("/api/v1/auth/register", json=user_data)
    user_data["username"] = "user2"
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    user_data = {"email": "u1@example.com", "username": "sameuser", "password": "password123"}
    await client.post("/api/v1/auth/register", json=user_data)
    user_data["email"] = "u2@example.com"
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "password123",
    })
    # Login
    response = await client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wrong@example.com",
        "username": "wronguser",
        "password": "password123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "wronguser",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "password123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "username": "refreshuser",
        "password": "password123",
    })
    login_response = await client.post("/api/v1/auth/login", json={
        "username": "refreshuser",
        "password": "password123",
    })
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "invalid-token",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_request(client: AsyncClient):
    response = await client.post("/api/v1/auth/password-reset", json={
        "email": "anyone@example.com",
    })
    # Always returns 202 to prevent email enumeration
    assert response.status_code == 202
