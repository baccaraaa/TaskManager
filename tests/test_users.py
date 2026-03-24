import pytest
from httpx import AsyncClient
from app.db.models import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user: User):
    response = await client.get("/api/v1/users/me", headers=auth_headers(test_user))
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["username"] == test_user.username


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 403  # No Bearer token


@pytest.mark.asyncio
async def test_update_current_user(client: AsyncClient, test_user: User):
    response = await client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=auth_headers(test_user),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, admin_user: User, test_user: User):
    response = await client.get("/api/v1/users/", headers=auth_headers(admin_user))
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client: AsyncClient, test_user: User):
    response = await client.get("/api/v1/users/", headers=auth_headers(test_user))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_get_user_by_id(client: AsyncClient, admin_user: User, test_user: User):
    response = await client.get(
        f"/api/v1/users/{test_user.id}", headers=auth_headers(admin_user)
    )
    assert response.status_code == 200
    assert response.json()["username"] == test_user.username
