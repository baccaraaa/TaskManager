"""Direct unit tests for service layer functions."""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, create_password_reset_token, create_refresh_token
from app.crud import project as project_crud
from app.crud import task as task_crud
from app.db.models import User, Project, Task, UserRole, TaskStatus, TaskPriority
from app.schemas.project import ProjectCreate
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters
from app.schemas.user import UserCreate
from app.services import auth as auth_service
from app.services import project as project_service
from app.services import task as task_service


# ---- Fixtures ----

@pytest_asyncio.fixture
async def service_user(db_session: AsyncSession) -> User:
    """Create a user for service tests."""
    user = User(
        email="svc@example.com",
        username="svcuser",
        full_name="Service User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def service_project(db_session: AsyncSession, service_user: User) -> Project:
    project_in = ProjectCreate(name="Svc Project")
    return await project_crud.create_project(db_session, project_in, service_user.id)


@pytest_asyncio.fixture
async def service_task(db_session: AsyncSession, service_user: User, service_project: Project) -> Task:
    task_in = TaskCreate(title="Svc Task", project_id=service_project.id)
    return await task_crud.create_task(db_session, task_in, service_user.id)


# ---- Auth Service ----

@pytest.mark.asyncio
async def test_register_user(db_session: AsyncSession):
    user_in = UserCreate(
        email="register@example.com",
        username="registeruser",
        password="password123",
    )
    with patch("app.services.auth.send_welcome_email", create=True):
        user = await auth_service.register_user(db_session, user_in)
    assert user.email == "register@example.com"
    assert user.username == "registeruser"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(db_session: AsyncSession, service_user: User):
    user_in = UserCreate(
        email=service_user.email,
        username="newusername",
        password="password123",
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(db_session, user_in)
    assert exc_info.value.status_code == 409
    assert "Email already registered" in exc_info.value.detail


@pytest.mark.asyncio
async def test_register_user_duplicate_username(db_session: AsyncSession, service_user: User):
    user_in = UserCreate(
        email="unique@example.com",
        username=service_user.username,
        password="password123",
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(db_session, user_in)
    assert exc_info.value.status_code == 409
    assert "Username already taken" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession, service_user: User):
    user = await auth_service.authenticate_user(db_session, "svcuser", "testpassword123")
    assert user.id == service_user.id


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession, service_user: User):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(db_session, "svcuser", "wrongpassword")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_user_nonexistent(db_session: AsyncSession):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(db_session, "nobody", "password123")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_user_inactive(db_session: AsyncSession):
    user = User(
        email="inactive@example.com",
        username="inactiveuser",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate_user(db_session, "inactiveuser", "password123")
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail


def test_create_tokens(service_user: User):
    token = auth_service.create_tokens(service_user)
    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_refresh_access_token(db_session: AsyncSession, service_user: User):
    refresh_token = create_refresh_token(data={"sub": service_user.username})
    new_tokens = await auth_service.refresh_access_token(db_session, refresh_token)
    assert new_tokens.access_token is not None
    assert new_tokens.refresh_token is not None


@pytest.mark.asyncio
async def test_refresh_access_token_invalid(db_session: AsyncSession):
    with pytest.raises(HTTPException):
        await auth_service.refresh_access_token(db_session, "invalid-token")


@pytest.mark.asyncio
async def test_refresh_access_token_user_not_found(db_session: AsyncSession):
    refresh_token = create_refresh_token(data={"sub": "nonexistent"})
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.refresh_access_token(db_session, refresh_token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_request_password_reset_existing_user(db_session: AsyncSession, service_user: User):
    # Should not raise even for existing user
    await auth_service.request_password_reset(db_session, service_user.email)


@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_email(db_session: AsyncSession):
    # Should not raise for non-existing email either
    await auth_service.request_password_reset(db_session, "nonexistent@example.com")


@pytest.mark.asyncio
async def test_confirm_password_reset_success(db_session: AsyncSession, service_user: User):
    token = create_password_reset_token(service_user.email)
    await auth_service.confirm_password_reset(db_session, token, "newpassword123")
    # Verify the password was changed
    user = await auth_service.authenticate_user(db_session, service_user.username, "newpassword123")
    assert user.id == service_user.id


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_token(db_session: AsyncSession):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.confirm_password_reset(db_session, "invalid-token", "newpass123")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_password_reset_user_not_found(db_session: AsyncSession):
    token = create_password_reset_token("nonexistent@example.com")
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.confirm_password_reset(db_session, token, "newpass123")
    assert exc_info.value.status_code == 404


# ---- Project Service ----

@pytest.mark.asyncio
async def test_create_project_service(db_session: AsyncSession, service_user: User):
    project_in = ProjectCreate(name="Service Project")
    project = await project_service.create_project(db_session, project_in, service_user)
    assert project.name == "Service Project"
    assert project.owner_id == service_user.id


@pytest.mark.asyncio
async def test_get_user_projects_service(db_session: AsyncSession, service_user: User, service_project: Project):
    projects = await project_service.get_user_projects(db_session, service_user)
    assert len(projects) >= 1


@pytest.mark.asyncio
async def test_get_project_or_403_success(db_session: AsyncSession, service_user: User, service_project: Project):
    project = await project_service.get_project_or_403(db_session, service_project.id, service_user)
    assert project.id == service_project.id


@pytest.mark.asyncio
async def test_get_project_or_403_not_found(db_session: AsyncSession, service_user: User):
    with pytest.raises(HTTPException) as exc_info:
        await project_service.get_project_or_403(db_session, 99999, service_user)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_project_or_403_forbidden(db_session: AsyncSession, service_user: User, service_project: Project):
    other_user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.USER,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    with pytest.raises(HTTPException) as exc_info:
        await project_service.get_project_or_403(db_session, service_project.id, other_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_project_service(db_session: AsyncSession, service_user: User, service_project: Project):
    from app.schemas.project import ProjectUpdate
    update_in = ProjectUpdate(name="Updated via Service")
    updated = await project_service.update_project(db_session, service_project.id, update_in, service_user)
    assert updated.name == "Updated via Service"


@pytest.mark.asyncio
async def test_delete_project_service(db_session: AsyncSession, service_user: User):
    project_in = ProjectCreate(name="To Delete via Service")
    project = await project_service.create_project(db_session, project_in, service_user)
    await project_service.delete_project(db_session, project.id, service_user)
    with pytest.raises(HTTPException):
        await project_service.get_project_or_403(db_session, project.id, service_user)


# ---- Task Service ----

@pytest.mark.asyncio
async def test_create_task_service(db_session: AsyncSession, service_user: User, service_project: Project):
    task_in = TaskCreate(title="Service Task", project_id=service_project.id)
    task = await task_service.create_task(db_session, task_in, service_user)
    assert task.title == "Service Task"
    assert task.project_id == service_project.id


@pytest.mark.asyncio
async def test_create_task_service_forbidden(db_session: AsyncSession, service_user: User, service_project: Project):
    other_user = User(
        email="other2@example.com",
        username="otheruser2",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.USER,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    task_in = TaskCreate(title="Sneaky", project_id=service_project.id)
    with pytest.raises(HTTPException) as exc_info:
        await task_service.create_task(db_session, task_in, other_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_tasks_service(db_session: AsyncSession, service_user: User, service_project: Project, service_task: Task):
    filters = TaskFilters()
    tasks, total = await task_service.get_tasks(db_session, filters, service_user)
    assert total >= 1


@pytest.mark.asyncio
async def test_get_task_or_403_success(db_session: AsyncSession, service_user: User, service_task: Task):
    task = await task_service.get_task_or_403(db_session, service_task.id, service_user)
    assert task.id == service_task.id


@pytest.mark.asyncio
async def test_get_task_or_403_not_found(db_session: AsyncSession, service_user: User):
    with pytest.raises(HTTPException) as exc_info:
        await task_service.get_task_or_403(db_session, 99999, service_user)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_task_or_403_forbidden(db_session: AsyncSession, service_user: User, service_task: Task):
    other_user = User(
        email="other3@example.com",
        username="otheruser3",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        role=UserRole.USER,
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    with pytest.raises(HTTPException) as exc_info:
        await task_service.get_task_or_403(db_session, service_task.id, other_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_task_service(db_session: AsyncSession, service_user: User, service_task: Task):
    update_in = TaskUpdate(title="Updated Task Title")
    updated = await task_service.update_task(db_session, service_task.id, update_in, service_user)
    assert updated.title == "Updated Task Title"


@pytest.mark.asyncio
async def test_update_task_status_change(db_session: AsyncSession, service_user: User, service_task: Task):
    update_in = TaskUpdate(status=TaskStatus.IN_PROGRESS)
    updated = await task_service.update_task(db_session, service_task.id, update_in, service_user)
    assert updated.status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_delete_task_service(db_session: AsyncSession, service_user: User, service_project: Project):
    task_in = TaskCreate(title="To Delete", project_id=service_project.id)
    task = await task_service.create_task(db_session, task_in, service_user)
    await task_service.delete_task(db_session, task.id, service_user)
    with pytest.raises(HTTPException):
        await task_service.get_task_or_403(db_session, task.id, service_user)
