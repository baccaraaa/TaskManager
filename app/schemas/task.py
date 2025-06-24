from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.models import TaskStatus, TaskPriority
from app.schemas.user import User
from app.schemas.project import Project


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    project_id: int
    assignee_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None


class TaskInDB(TaskBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    project_id: int
    assignee_id: Optional[int] = None
    created_by_id: int

    class Config:
        from_attributes = True


class Task(TaskInDB):
    project: Project
    assignee: Optional[User] = None
    created_by: User


class TaskAttachmentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    content_type: str


class TaskAttachmentInDB(TaskAttachmentBase):
    id: int
    file_path: str
    created_at: datetime
    task_id: int
    uploaded_by_id: int

    class Config:
        from_attributes = True


class TaskAttachment(TaskAttachmentInDB):
    uploaded_by: User


class TaskWithAttachments(Task):
    attachments: List[TaskAttachment] = []


# Query parameters for filtering tasks
class TaskFilters(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    search: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)
