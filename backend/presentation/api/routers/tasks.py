from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from backend.presentation.api.dependencies import get_current_user
from backend.infrastructure.database.models import User, Task
from backend.infrastructure.database.session import db_manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[str] = "medium"

class TaskUpdateStatus(BaseModel):
    status: str

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    deadline: Optional[datetime]
    status: str
    priority: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[TaskResponse])
async def list_tasks(current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        stmt = select(Task).where(
            Task.user_id == current_user.id,
            Task.is_deleted == False
        ).order_by(Task.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

@router.post("", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        deadline_utc = None
        if task_in.deadline:
            deadline_utc = task_in.deadline.astimezone(timezone.utc).replace(tzinfo=None)

        new_task = Task(
            user_id=current_user.id,
            source_origin="user_ui",
            title=task_in.title,
            description=task_in.description,
            deadline=deadline_utc,
            priority=task_in.priority,
            status="pending",
            is_deleted=False
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        return new_task

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task_status(task_id: str, task_in: TaskUpdateStatus, current_user: User = Depends(get_current_user)):
    if task_in.status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    async with db_manager.session() as db:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        task.status = task_in.status
        task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        await db.refresh(task)
        return task

@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Soft delete
        task.is_deleted = True
        task.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        return {"success": True}
