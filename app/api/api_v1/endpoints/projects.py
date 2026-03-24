from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.crud import project as project_crud
from app.db.database import get_async_session
from app.db.models import User
from app.schemas.project import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectInDB,
    ProjectUpdate,
    ProjectWithStats,
)
from app.services import project as project_service

router = APIRouter()


@router.get("/", response_model=list[ProjectInDB])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await project_service.get_user_projects(db, current_user, skip, limit)


@router.post("/", response_model=ProjectInDB, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await project_service.create_project(db, project_in, current_user)


@router.get("/{project_id}", response_model=ProjectInDB)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await project_service.get_project_or_403(db, project_id, current_user)


@router.put("/{project_id}", response_model=ProjectInDB)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    return await project_service.update_project(db, project_id, project_in, current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user),
):
    await project_service.delete_project(db, project_id, current_user)
