import pytest
from httpx import AsyncClient
from app.db.models import User
from tests.conftest import auth_headers


async def _create_project(client: AsyncClient, user: User) -> int:
    resp = await client.post(
        "/api/v1/projects/", json={"name": "Test Project"}, headers=auth_headers(user)
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)

    response = await client.post("/api/v1/tasks/", json={
        "title": "My Task",
        "description": "Task description",
        "project_id": project_id,
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Task"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)

    await client.post("/api/v1/tasks/", json={"title": "Task 1", "project_id": project_id}, headers=headers)
    await client.post("/api/v1/tasks/", json={"title": "Task 2", "project_id": project_id}, headers=headers)

    response = await client.get("/api/v1/tasks/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/tasks/", json={"title": "Get Me", "project_id": project_id}, headers=headers
    )
    task_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/tasks/", json={"title": "Update Me", "project_id": project_id}, headers=headers
    )
    task_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/tasks/{task_id}", json={
        "title": "Updated Title",
        "status": "in_progress",
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_complete_task_sets_completed_at(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/tasks/", json={"title": "Complete Me", "project_id": project_id}, headers=headers
    )
    task_id = create_resp.json()["id"]

    response = await client.put(f"/api/v1/tasks/{task_id}", json={
        "status": "completed",
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)
    create_resp = await client.post(
        "/api/v1/tasks/", json={"title": "Delete Me", "project_id": project_id}, headers=headers
    )
    task_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_filter_tasks_by_status(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)

    await client.post("/api/v1/tasks/", json={"title": "Todo", "project_id": project_id}, headers=headers)
    create_resp = await client.post(
        "/api/v1/tasks/", json={"title": "Done", "project_id": project_id}, headers=headers
    )
    task_id = create_resp.json()["id"]
    await client.put(f"/api/v1/tasks/{task_id}", json={"status": "completed"}, headers=headers)

    response = await client.get("/api/v1/tasks/?status=completed", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Done"


@pytest.mark.asyncio
async def test_search_tasks(client: AsyncClient, test_user: User):
    project_id = await _create_project(client, test_user)
    headers = auth_headers(test_user)

    await client.post("/api/v1/tasks/", json={"title": "Fix login bug", "project_id": project_id}, headers=headers)
    await client.post("/api/v1/tasks/", json={"title": "Add feature", "project_id": project_id}, headers=headers)

    response = await client.get("/api/v1/tasks/?search=bug", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_cannot_create_task_in_others_project(client: AsyncClient, test_user: User, admin_user: User):
    # Create project as test_user
    project_id = await _create_project(client, test_user)

    # Try to create task as admin_user in test_user's project
    response = await client.post("/api/v1/tasks/", json={
        "title": "Sneaky Task",
        "project_id": project_id,
    }, headers=auth_headers(admin_user))
    assert response.status_code == 403
