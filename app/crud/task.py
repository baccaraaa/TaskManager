from datetime import datetime, timezone

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, TaskAttachment, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks(
    db: AsyncSession,
    filters: TaskFilters,
    user_project_ids: list[int] | None = None,
) -> tuple[list[Task], int]:
    query = select(Task)
    count_query = select(func.count(Task.id))

    if user_project_ids is not None:
        query = query.where(Task.project_id.in_(user_project_ids))
        count_query = count_query.where(Task.project_id.in_(user_project_ids))

    if filters.status is not None:
        query = query.where(Task.status == filters.status)
        count_query = count_query.where(Task.status == filters.status)

    if filters.priority is not None:
        query = query.where(Task.priority == filters.priority)
        count_query = count_query.where(Task.priority == filters.priority)

    if filters.assignee_id is not None:
        query = query.where(Task.assignee_id == filters.assignee_id)
        count_query = count_query.where(Task.assignee_id == filters.assignee_id)

    if filters.project_id is not None:
        query = query.where(Task.project_id == filters.project_id)
        count_query = count_query.where(Task.project_id == filters.project_id)

    if filters.due_before is not None:
        query = query.where(Task.due_date <= filters.due_before)
        count_query = count_query.where(Task.due_date <= filters.due_before)

    if filters.due_after is not None:
        query = query.where(Task.due_date >= filters.due_after)
        count_query = count_query.where(Task.due_date >= filters.due_after)

    if filters.search is not None:
        search_term = f"%{filters.search}%"
        search_filter = or_(
            Task.title.ilike(search_term),
            Task.description.ilike(search_term),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(filters.skip).limit(filters.limit)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return tasks, total


async def create_task(
    db: AsyncSession, task_in: TaskCreate, created_by_id: int
) -> Task:
    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        project_id=task_in.project_id,
        assignee_id=task_in.assignee_id,
        created_by_id=created_by_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession, task: Task, task_in: TaskUpdate
) -> Task:
    update_data = task_in.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            task.completed_at = datetime.now(timezone.utc)
        elif new_status != TaskStatus.COMPLETED and task.status == TaskStatus.COMPLETED:
            task.completed_at = None

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()


async def create_attachment(
    db: AsyncSession,
    task_id: int,
    uploaded_by_id: int,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    content_type: str,
) -> TaskAttachment:
    attachment = TaskAttachment(
        task_id=task_id,
        uploaded_by_id=uploaded_by_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        content_type=content_type,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def get_attachment(
    db: AsyncSession, attachment_id: int
) -> TaskAttachment | None:
    result = await db.execute(
        select(TaskAttachment).where(TaskAttachment.id == attachment_id)
    )
    return result.scalar_one_or_none()
