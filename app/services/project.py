from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import project as project_crud
from app.db.models import Project, User
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(db: AsyncSession, project_in: ProjectCreate, current_user: User) -> Project:
    return await project_crud.create_project(db, project_in, current_user.id)


async def get_user_projects(
    db: AsyncSession, current_user: User, skip: int = 0, limit: int = 100
) -> list[Project]:
    return await project_crud.get_projects_by_owner(db, current_user.id, skip, limit)


async def get_project_or_403(db: AsyncSession, project_id: int, current_user: User) -> Project:
    """Get project and verify ownership."""
    project = await project_crud.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return project


async def update_project(
    db: AsyncSession, project_id: int, project_in: ProjectUpdate, current_user: User
) -> Project:
    project = await get_project_or_403(db, project_id, current_user)
    return await project_crud.update_project(db, project, project_in)


async def delete_project(db: AsyncSession, project_id: int, current_user: User) -> None:
    project = await get_project_or_403(db, project_id, current_user)
    await project_crud.delete_project(db, project)
