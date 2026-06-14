from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from backend.presentation.api.dependencies import get_current_user
from backend.infrastructure.database.models import User, CalendarEvent
from backend.infrastructure.database.session import db_manager

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

class CalendarEventCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

class CalendarEventResponse(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[CalendarEventResponse])
async def list_events(current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        stmt = select(CalendarEvent).where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.is_deleted == False
        ).order_by(CalendarEvent.start_time.asc())
        result = await db.execute(stmt)
        return result.scalars().all()

@router.post("", response_model=CalendarEventResponse)
async def create_event(event_in: CalendarEventCreate, current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        new_event = CalendarEvent(
            user_id=current_user.id,
            source_origin="user_ui",
            title=event_in.title,
            start_time=event_in.start_time.astimezone(timezone.utc).replace(tzinfo=None),
            end_time=event_in.end_time.astimezone(timezone.utc).replace(tzinfo=None),
            location=event_in.location,
            is_deleted=False
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        return new_event

@router.delete("/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    async with db_manager.session() as db:
        stmt = select(CalendarEvent).where(CalendarEvent.id == event_id, CalendarEvent.user_id == current_user.id)
        result = await db.execute(stmt)
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Soft delete
        event.is_deleted = True
        event.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        return {"success": True}
