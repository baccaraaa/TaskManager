"""Direct unit tests for CRUD operations, bypassing the HTTP layer."""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.crud import user as user_crud
from app.crud import project as project_crud
from app.crud import task as task_crud
from app.db.models import User, Project, Task, UserRole, TaskStatus, TaskPriority
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters


# ---- User CRUD ----

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user_in = UserCreate(
        email="crud@example.com",
        username="cruduser",
        password="password123",
    )
    user = await user_crud.create_user(db_session, user_in)
    assert user.email == "crud@example.com"
    assert user.username == "cruduser"
    assert user.hashed_password != "password123"


@pytest.mark.asyncio
async def test_get_user(db_session: AsyncSession, test_user: User):
    fetched = await user_crud.get_user(db_session, test_user.id)
    assert fetched is not None
    assert fetched.id == test_user.id


@pytest.mark.asyncio
async def test_get_user_not_found(db_session: AsyncSession):
    fetched = await user_crud.get_user(db_session, 99999)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession, test_user: User):
    fetched = await user_crud.get_user_by_email(db_session, test_user.email)
    assert fetched is not None
    assert fetched.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession):
    fetched = await user_crud.get_user_by_email(db_session, "nobody@example.com")
    assert fetched is None


@pytest.mark.asyncio
async def test_get_user_by_username(db_session: AsyncSession, test_user: User):
    fetched = await user_crud.get_user_by_username(db_session, test_user.username)
    assert fetched is not None
    assert fetched.username == test_user.username


@pytest.mark.asyncio
async def test_get_user_by_username_not_found(db_session: AsyncSession):
    fetched = await user_crud.get_user_by_username(db_session, "nonexistent")
    assert fetched is None


@pytest.mark.asyncio
async def test_get_users(db_session: AsyncSession, test_user: User, admin_user: User):
    users = await user_crud.get_users(db_session)
    assert len(users) >= 2


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession, test_user: User):
    update_in = UserUpdate(full_name="New Full Name")
    updated = await user_crud.update_user(db_session, test_user, update_in)
    assert updated.full_name == "New Full Name"


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession):
    user_in = UserCreate(
        email="delete@example.com",
        username="deleteuser",
        password="password123",
    )
    user = await user_crud.create_user(db_session, user_in)
    await user_crud.delete_user(db_session, user)
    fetched = await user_crud.get_user(db_session, user.id)
    assert fetched is None


# ---- Project CRUD ----

@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    project_in = ProjectCreate(name="Test Project", description="A test project")
    return await project_crud.create_project(db_session, project_in, test_user.id)


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession, test_user: User):
    project_in = ProjectCreate(name="New Proj", description="desc")
    project = await project_crud.create_project(db_session, project_in, test_user.id)
    assert project.name == "New Proj"
    assert project.owner_id == test_user.id


@pytest.mark.asyncio
async def test_get_project(db_session: AsyncSession, test_project: Project):
    fetched = await project_crud.get_project(db_session, test_project.id)
    assert fetched is not None
    assert fetched.name == test_project.name


@pytest.mark.asyncio
async def test_get_project_not_found(db_session: AsyncSession):
    fetched = await project_crud.get_project(db_session, 99999)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_projects_by_owner(db_session: AsyncSession, test_user: User, test_project: Project):
    projects = await project_crud.get_projects_by_owner(db_session, test_user.id)
    assert len(projects) >= 1
    assert any(p.id == test_project.id for p in projects)


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession, test_project: Project):
    update_in = ProjectUpdate(name="Updated Name")
    updated = await project_crud.update_project(db_session, test_project, update_in)
    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession, test_user: User):
    project_in = ProjectCreate(name="To Delete")
    project = await project_crud.create_project(db_session, project_in, test_user.id)
    await project_crud.delete_project(db_session, project)
    fetched = await project_crud.get_project(db_session, project.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_project_stats(db_session: AsyncSession, test_user: User, test_project: Project):
    # Create tasks with different statuses
    task1 = Task(
        title="Todo Task", project_id=test_project.id,
        created_by_id=test_user.id, status=TaskStatus.TODO,
    )
    task2 = Task(
        title="In Progress", project_id=test_project.id,
        created_by_id=test_user.id, status=TaskStatus.IN_PROGRESS,
    )
    task3 = Task(
        title="Completed", project_id=test_project.id,
        created_by_id=test_user.id, status=TaskStatus.COMPLETED,
    )
    db_session.add_all([task1, task2, task3])
    await db_session.commit()

    stats = await project_crud.get_project_stats(db_session, test_project.id)
    assert stats["total_tasks"] == 3
    assert stats["todo_tasks"] == 1
    assert stats["in_progress_tasks"] == 1
    assert stats["completed_tasks"] == 1


# ---- Task CRUD ----

@pytest_asyncio.fixture
async def test_task(db_session: AsyncSession, test_user: User, test_project: Project) -> Task:
    task_in = TaskCreate(
        title="Test Task",
        description="A test task",
        project_id=test_project.id,
    )
    return await task_crud.create_task(db_session, task_in, test_user.id)


@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession, test_user: User, test_project: Project):
    task_in = TaskCreate(
        title="New Task", description="desc", project_id=test_project.id,
    )
    task = await task_crud.create_task(db_session, task_in, test_user.id)
    assert task.title == "New Task"
    assert task.status == TaskStatus.TODO
    assert task.priority == TaskPriority.MEDIUM


@pytest.mark.asyncio
async def test_get_task(db_session: AsyncSession, test_task: Task):
    fetched = await task_crud.get_task(db_session, test_task.id)
    assert fetched is not None
    assert fetched.title == test_task.title


@pytest.mark.asyncio
async def test_get_task_not_found(db_session: AsyncSession):
    fetched = await task_crud.get_task(db_session, 99999)
    assert fetched is None


@pytest.mark.asyncio
async def test_update_task_status_to_completed(db_session: AsyncSession, test_task: Task):
    update_in = TaskUpdate(status=TaskStatus.COMPLETED)
    updated = await task_crud.update_task(db_session, test_task, update_in)
    assert updated.status == TaskStatus.COMPLETED
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_update_task_status_from_completed(db_session: AsyncSession, test_task: Task):
    # First complete the task
    update_in = TaskUpdate(status=TaskStatus.COMPLETED)
    updated = await task_crud.update_task(db_session, test_task, update_in)
    assert updated.completed_at is not None

    # Then revert to in_progress
    update_in2 = TaskUpdate(status=TaskStatus.IN_PROGRESS)
    updated2 = await task_crud.update_task(db_session, updated, update_in2)
    assert updated2.status == TaskStatus.IN_PROGRESS
    assert updated2.completed_at is None


@pytest.mark.asyncio
async def test_update_task_title(db_session: AsyncSession, test_task: Task):
    update_in = TaskUpdate(title="Updated Title")
    updated = await task_crud.update_task(db_session, test_task, update_in)
    assert updated.title == "Updated Title"


@pytest.mark.asyncio
async def test_delete_task(db_session: AsyncSession, test_user: User, test_project: Project):
    task_in = TaskCreate(title="To Delete", project_id=test_project.id)
    task = await task_crud.create_task(db_session, task_in, test_user.id)
    await task_crud.delete_task(db_session, task)
    fetched = await task_crud.get_task(db_session, task.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_tasks_no_filters(db_session: AsyncSession, test_user: User, test_project: Project):
    # Create a couple of tasks
    for i in range(3):
        task_in = TaskCreate(title=f"Task {i}", project_id=test_project.id)
        await task_crud.create_task(db_session, task_in, test_user.id)

    filters = TaskFilters()
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 3
    assert len(tasks) == 3


@pytest.mark.asyncio
async def test_get_tasks_filter_by_status(db_session: AsyncSession, test_user: User, test_project: Project):
    t1 = TaskCreate(title="Todo", project_id=test_project.id, status=TaskStatus.TODO)
    t2 = TaskCreate(title="Done", project_id=test_project.id, status=TaskStatus.COMPLETED)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)

    filters = TaskFilters(status=TaskStatus.COMPLETED)
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 1
    assert tasks[0].title == "Done"


@pytest.mark.asyncio
async def test_get_tasks_filter_by_priority(db_session: AsyncSession, test_user: User, test_project: Project):
    t1 = TaskCreate(title="Low", project_id=test_project.id, priority=TaskPriority.LOW)
    t2 = TaskCreate(title="High", project_id=test_project.id, priority=TaskPriority.HIGH)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)

    filters = TaskFilters(priority=TaskPriority.HIGH)
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 1
    assert tasks[0].title == "High"


@pytest.mark.asyncio
async def test_get_tasks_filter_by_assignee(db_session: AsyncSession, test_user: User, test_project: Project):
    t1 = TaskCreate(title="Assigned", project_id=test_project.id, assignee_id=test_user.id)
    t2 = TaskCreate(title="Unassigned", project_id=test_project.id)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)

    filters = TaskFilters(assignee_id=test_user.id)
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 1
    assert tasks[0].title == "Assigned"


@pytest.mark.asyncio
async def test_get_tasks_filter_by_project_id(db_session: AsyncSession, test_user: User, test_project: Project):
    # Create a second project
    p2 = await project_crud.create_project(
        db_session, ProjectCreate(name="Other"), test_user.id
    )
    t1 = TaskCreate(title="In P1", project_id=test_project.id)
    t2 = TaskCreate(title="In P2", project_id=p2.id)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)

    filters = TaskFilters(project_id=test_project.id)
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id, p2.id])
    assert total == 1
    assert tasks[0].title == "In P1"


@pytest.mark.asyncio
async def test_get_tasks_filter_by_due_date(db_session: AsyncSession, test_user: User, test_project: Project):
    early = datetime(2025, 1, 1, tzinfo=timezone.utc)
    late = datetime(2025, 12, 31, tzinfo=timezone.utc)
    t1 = TaskCreate(title="Early", project_id=test_project.id, due_date=early)
    t2 = TaskCreate(title="Late", project_id=test_project.id, due_date=late)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)

    # due_before
    filters = TaskFilters(due_before=datetime(2025, 6, 1, tzinfo=timezone.utc))
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 1
    assert tasks[0].title == "Early"

    # due_after
    filters2 = TaskFilters(due_after=datetime(2025, 6, 1, tzinfo=timezone.utc))
    tasks2, total2 = await task_crud.get_tasks(db_session, filters2, [test_project.id])
    assert total2 == 1
    assert tasks2[0].title == "Late"


@pytest.mark.asyncio
async def test_get_tasks_search(db_session: AsyncSession, test_user: User, test_project: Project):
    t1 = TaskCreate(title="Fix login bug", project_id=test_project.id)
    t2 = TaskCreate(title="Add feature", description="important bug fix", project_id=test_project.id)
    t3 = TaskCreate(title="Deploy app", project_id=test_project.id)
    await task_crud.create_task(db_session, t1, test_user.id)
    await task_crud.create_task(db_session, t2, test_user.id)
    await task_crud.create_task(db_session, t3, test_user.id)

    filters = TaskFilters(search="bug")
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 2  # title match + description match


@pytest.mark.asyncio
async def test_get_tasks_pagination(db_session: AsyncSession, test_user: User, test_project: Project):
    for i in range(5):
        t = TaskCreate(title=f"Task {i}", project_id=test_project.id)
        await task_crud.create_task(db_session, t, test_user.id)

    filters = TaskFilters(skip=2, limit=2)
    tasks, total = await task_crud.get_tasks(db_session, filters, [test_project.id])
    assert total == 5
    assert len(tasks) == 2


@pytest.mark.asyncio
async def test_create_and_get_attachment(db_session: AsyncSession, test_user: User, test_task: Task):
    attachment = await task_crud.create_attachment(
        db=db_session,
        task_id=test_task.id,
        uploaded_by_id=test_user.id,
        filename="abc123.txt",
        original_filename="readme.txt",
        file_path="/tmp/uploads/abc123.txt",
        file_size=1024,
        content_type="text/plain",
    )
    assert attachment.filename == "abc123.txt"
    assert attachment.task_id == test_task.id

    fetched = await task_crud.get_attachment(db_session, attachment.id)
    assert fetched is not None
    assert fetched.id == attachment.id


@pytest.mark.asyncio
async def test_get_attachment_not_found(db_session: AsyncSession):
    fetched = await task_crud.get_attachment(db_session, 99999)
    assert fetched is None
