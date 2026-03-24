import pytest
from httpx import AsyncClient
from app.db.models import User
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/projects/",
        json={"name": "My Project", "description": "A test project"},
        headers=auth_headers(test_user),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert data["owner_id"] == test_user.id


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, test_user: User):
    headers = auth_headers(test_user)
    await client.post("/api/v1/projects/", json={"name": "Proj 1"}, headers=headers)
    await client.post("/api/v1/projects/", json={"name": "Proj 2"}, headers=headers)

    response = await client.get("/api/v1/projects/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, test_user: User):
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/projects/", json={"name": "Get Me"}, headers=headers
    )
    project_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Get Me"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, test_user: User):
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/projects/", json={"name": "Old Name"}, headers=headers
    )
    project_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, test_user: User):
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/projects/", json={"name": "Delete Me"}, headers=headers
    )
    project_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_access_other_users_project(client: AsyncClient, test_user: User, admin_user: User):
    # Create project as test_user
    create_resp = await client.post(
        "/api/v1/projects/", json={"name": "Private"}, headers=auth_headers(test_user)
    )
    project_id = create_resp.json()["id"]

    # Try to access as admin_user (who doesn't own it)
    response = await client.get(
        f"/api/v1/projects/{project_id}", headers=auth_headers(admin_user)
    )
    assert response.status_code == 403
