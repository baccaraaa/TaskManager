import os
import uuid
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import task as task_crud
from app.crud import project as project_crud
from app.db.models import Task, User, TaskAttachment
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilters


async def _get_user_project_ids(db: AsyncSession, user: User) -> list[int]:
    """Get list of project IDs owned by user."""
    projects = await project_crud.get_projects_by_owner(db, user.id, skip=0, limit=10000)
    return [p.id for p in projects]


async def create_task(db: AsyncSession, task_in: TaskCreate, current_user: User) -> Task:
    # Verify user owns the project
    project = await project_crud.get_project(db, task_in.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this project",
        )
    task = await task_crud.create_task(db, task_in, current_user.id)

    # Notify assignee via WebSocket
    if task.assignee_id:
        try:
            from app.services.websocket import manager
            await manager.send_personal(
                {"event": "task_assigned", "task_id": task.id, "title": task.title},
                task.assignee_id,
            )
        except Exception:
            pass

    return task


async def get_tasks(
    db: AsyncSession, filters: TaskFilters, current_user: User
) -> tuple[list[Task], int]:
    project_ids = await _get_user_project_ids(db, current_user)
    return await task_crud.get_tasks(db, filters, project_ids)


async def get_task_or_403(db: AsyncSession, task_id: int, current_user: User) -> Task:
    task = await task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    project = await project_crud.get_project(db, task.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return task


async def update_task(
    db: AsyncSession, task_id: int, task_in: TaskUpdate, current_user: User
) -> Task:
    task = await get_task_or_403(db, task_id, current_user)
    old_status = task.status
    updated_task = await task_crud.update_task(db, task, task_in)

    # Notify via WebSocket on status change
    if task_in.status and task_in.status != old_status:
        try:
            from app.services.websocket import manager
            notify_user_id = updated_task.assignee_id or current_user.id
            await manager.send_personal(
                {
                    "event": "task_status_changed",
                    "task_id": updated_task.id,
                    "title": updated_task.title,
                    "old_status": old_status.value,
                    "new_status": updated_task.status.value,
                },
                notify_user_id,
            )
        except Exception:
            pass

    return updated_task


async def delete_task(db: AsyncSession, task_id: int, current_user: User) -> None:
    task = await get_task_or_403(db, task_id, current_user)
    await task_crud.delete_task(db, task)


async def upload_attachment(
    db: AsyncSession, task_id: int, file: UploadFile, current_user: User
) -> TaskAttachment:
    task = await get_task_or_403(db, task_id, current_user)

    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes",
        )

    # Save file
    file_ext = os.path.splitext(file.filename or "file")[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    return await task_crud.create_attachment(
        db=db,
        task_id=task_id,
        uploaded_by_id=current_user.id,
        filename=unique_filename,
        original_filename=file.filename or "file",
        file_path=file_path,
        file_size=len(content),
        content_type=file.content_type or "application/octet-stream",
    )


async def get_attachment_or_404(
    db: AsyncSession, attachment_id: int, current_user: User
) -> TaskAttachment:
    attachment = await task_crud.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found",
        )
    # Verify access through task -> project ownership
    await get_task_or_403(db, attachment.task_id, current_user)
    return attachment
