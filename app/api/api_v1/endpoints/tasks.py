from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.database import get_async_session
from app.db.models import User, TaskStatus, TaskPriority
from app.schemas.task import (
    Task as TaskSchema,
    TaskCreate,
    TaskInDB,
    TaskUpdate,
    TaskFilters,
    TaskWithAttachments,
    TaskAttachmentInDB,
)
from app.services import task as task_service

router = APIRouter()


@router.get("/")
async def list_tasks(
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = None,
    assignee_id: int | None = None,
    project_id: int | None = None,
    due_before: str | None = None,
    due_after: str | None = None,
    search: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    filters = TaskFilters(
        status=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        project_id=project_id,
        due_before=datetime.fromisoformat(due_before) if due_before else None,
        due_after=datetime.fromisoformat(due_after) if due_after else None,
        search=search,
        skip=skip,
        limit=limit,
    )
    tasks, total = await task_service.get_tasks(db, filters, current_user)
    return {
        "items": [TaskInDB.model_validate(t) for t in tasks],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/", response_model=TaskInDB, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await task_service.create_task(db, task_in, current_user)


@router.get("/{task_id}", response_model=TaskInDB)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await task_service.get_task_or_403(db, task_id, current_user)


@router.put("/{task_id}", response_model=TaskInDB)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await task_service.update_task(db, task_id, task_in, current_user)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    await task_service.delete_task(db, task_id, current_user)


@router.post("/{task_id}/attachments", response_model=TaskAttachmentInDB, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await task_service.upload_attachment(db, task_id, file, current_user)


@router.get("/{task_id}/attachments/{attachment_id}")
async def download_attachment(
    task_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    attachment = await task_service.get_attachment_or_404(db, attachment_id, current_user)
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type,
    )
