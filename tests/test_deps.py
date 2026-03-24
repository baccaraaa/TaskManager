"""Tests for app.api.deps - authentication dependencies."""
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token, create_refresh_token
from app.db.models import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """Token that cannot be decoded should return 401."""
    headers = {"Authorization": "Bearer invalid-token-here"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_sub_in_token(client: AsyncClient):
    """Token without 'sub' claim should return 401."""
    token = create_access_token(data={})  # no sub
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_username(client: AsyncClient):
    """Token with a username that doesn't exist in the DB should return 401."""
    token = create_access_token(data={"sub": "ghost_user_doesnt_exist"})
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(client: AsyncClient, db_session):
    """Inactive user should get 400."""
    from app.core.security import get_password_hash
    from app.db.models import UserRole

    user = User(
        email="inactive_dep@example.com",
        username="inactivedep",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(data={"sub": "inactivedep"})
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user_refresh_token_rejected(client: AsyncClient, test_user: User):
    """Using a refresh token as access token should return 401."""
    token = create_refresh_token(data={"sub": test_user.username})
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_non_admin(client: AsyncClient, test_user: User):
    """Non-admin user should get 403 on admin endpoints."""
    response = await client.get("/api/v1/users/", headers=auth_headers(test_user))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_get_nonexistent_user(client: AsyncClient, admin_user: User):
    """Admin requesting non-existent user by ID should get 404."""
    response = await client.get("/api/v1/users/99999", headers=auth_headers(admin_user))
    assert response.status_code == 404
