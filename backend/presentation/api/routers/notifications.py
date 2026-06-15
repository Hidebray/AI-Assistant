from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete
from backend.presentation.api.dependencies import get_current_user, get_db_session
from backend.infrastructure.database.models import User, Notification
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"]
)

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    isRead: bool
    isImportant: bool
    createdAt: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = select(Notification).where(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc())
    
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    
    return [
        NotificationResponse(
            id=n.id,
            title=n.title,
            message=n.message,
            type=n.type,
            isRead=n.is_read,
            isImportant=n.is_important,
            createdAt=n.created_at
        ) for n in notifications
    ]

@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).values(is_read=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    stmt = delete(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    await db.commit()
    return {"message": "Notification deleted"}
