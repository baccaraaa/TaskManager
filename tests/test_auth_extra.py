"""Additional auth endpoint tests for better coverage."""
import pytest
from httpx import AsyncClient
from app.core.security import create_password_reset_token, create_access_token


@pytest.mark.asyncio
async def test_password_reset_confirm_success(client: AsyncClient):
    """Full password reset flow: register, get reset token, confirm reset, login with new password."""
    # Register a user
    await client.post("/api/v1/auth/register", json={
        "email": "resetme@example.com",
        "username": "resetme",
        "password": "oldpassword123",
    })

    # Create a reset token directly (simulating what the email would contain)
    reset_token = create_password_reset_token("resetme@example.com")

    # Confirm password reset
    response = await client.post("/api/v1/auth/password-reset/confirm", json={
        "token": reset_token,
        "new_password": "newpassword123",
    })
    assert response.status_code == 200

    # Login with new password
    login_response = await client.post("/api/v1/auth/login", json={
        "username": "resetme",
        "password": "newpassword123",
    })
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_confirm_invalid_token(client: AsyncClient):
    """Invalid reset token should return 400."""
    response = await client.post("/api/v1/auth/password-reset/confirm", json={
        "token": "invalid-token",
        "new_password": "newpassword123",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_confirm_wrong_token_type(client: AsyncClient):
    """Using an access token as a reset token should fail."""
    token = create_access_token(data={"sub": "testuser"})
    response = await client.post("/api/v1/auth/password-reset/confirm", json={
        "token": token,
        "new_password": "newpassword123",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_password_reset_confirm_nonexistent_email(client: AsyncClient):
    """Reset token for email not in DB should return 404."""
    reset_token = create_password_reset_token("nonexistent@example.com")
    response = await client.post("/api/v1/auth/password-reset/confirm", json={
        "token": reset_token,
        "new_password": "newpassword123",
    })
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_login_returns_token_type(client: AsyncClient):
    """Login should include token_type=bearer in response."""
    await client.post("/api/v1/auth/register", json={
        "email": "tokentype@example.com",
        "username": "tokentypeuser",
        "password": "password123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "tokentypeuser",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    """Using an access token where a refresh token is expected should fail."""
    await client.post("/api/v1/auth/register", json={
        "email": "accessfail@example.com",
        "username": "accessfailuser",
        "password": "password123",
    })
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "accessfailuser",
        "password": "password123",
    })
    access_token = login_resp.json()["access_token"]

    # Try to refresh using the access token instead of refresh token
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": access_token,
    })
    assert response.status_code == 401
