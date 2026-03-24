from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Task, TaskStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_projects_by_owner(
    db: AsyncSession, owner_id: int, skip: int = 0, limit: int = 100
) -> list[Project]:
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_project(
    db: AsyncSession, project_in: ProjectCreate, owner_id: int
) -> Project:
    project = Project(
        name=project_in.name,
        description=project_in.description,
        owner_id=owner_id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession, project: Project, project_in: ProjectUpdate
) -> Project:
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()


async def get_project_stats(db: AsyncSession, project_id: int) -> dict:
    result = await db.execute(
        select(
            func.count(Task.id).label("total_tasks"),
            func.count(Task.id)
            .filter(Task.status == TaskStatus.COMPLETED)
            .label("completed_tasks"),
            func.count(Task.id)
            .filter(Task.status == TaskStatus.IN_PROGRESS)
            .label("in_progress_tasks"),
            func.count(Task.id)
            .filter(Task.status == TaskStatus.TODO)
            .label("todo_tasks"),
        ).where(Task.project_id == project_id)
    )
    row = result.one()
    return {
        "total_tasks": row.total_tasks,
        "completed_tasks": row.completed_tasks,
        "in_progress_tasks": row.in_progress_tasks,
        "todo_tasks": row.todo_tasks,
    }
