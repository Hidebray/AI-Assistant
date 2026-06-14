import asyncio
import logging
import logging
from datetime import datetime, timezone
import dateutil.parser
from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import CalendarEvent, User

logger = logging.getLogger(__name__)

class CalendarPlugin(BasePlugin):
    def __init__(self):
        self.bus = None
        self.is_running = False

    def get_metadata(self) -> dict:
        return {
            "name": "calendar_plugin",
            "version": "1.0",
            "permissions": ["event_publish", "event_subscribe", "db_write"],
            "tools": [
                {
                    "name": "create_calendar_event",
                    "description": "Create a new calendar event or appointment.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user requesting the event."},
                            "title": {"type": "string", "description": "Title of the event"},
                            "start_time": {"type": "string", "format": "date-time", "description": "Start time. MUST BE LOCAL TIME. Format: YYYY-MM-DDTHH:MM:SS. DO NOT append 'Z' or timezone offset."},
                            "end_time": {"type": "string", "format": "date-time", "description": "End time. MUST BE LOCAL TIME. DO NOT append 'Z'."},
                            "location": {"type": "string", "description": "Location (optional)"}
                        },
                        "required": ["user_id", "title", "start_time", "end_time"]
                    }
                },
                {
                    "name": "get_calendar_events",
                    "description": "Retrieve the list of calendar events for the user within a specific time range.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "start_time": {"type": "string", "format": "date-time", "description": "Start time for the search range (ISO 8601)."},
                            "end_time": {"type": "string", "format": "date-time", "description": "End time for the search range (ISO 8601)."}
                        },
                        "required": ["user_id", "start_time", "end_time"]
                    }
                },
                {
                    "name": "clear_calendar_events",
                    "description": "Clear all calendar events for the user. Use only when the user explicitly requests to delete all events.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."}
                        },
                        "required": ["user_id"]
                    }
                },
                {
                    "name": "update_calendar_event",
                    "description": "Update the start time of an existing calendar event. Use when the user wants to reschedule or change the time of an appointment.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "title_keyword": {"type": "string", "description": "Keyword from the title of the event to reschedule."},
                            "new_start_time": {"type": "string", "format": "date-time", "description": "The new start time (ISO 8601)."}
                        },
                        "required": ["user_id", "title_keyword", "new_start_time"]
                    }
                },
                {
                    "name": "delete_calendar_event",
                    "description": "Delete or cancel a specific calendar event based on a title keyword.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "title_keyword": {"type": "string", "description": "Keyword from the title of the event to delete."}
                        },
                        "required": ["user_id", "title_keyword"]
                    }
                }
            ]
        }

    async def on_load(self):
        logger.info("[CalendarPlugin] Loaded configuration.")

    async def on_start(self, event_bus: IEventBus):
        self.bus = event_bus
        self.is_running = True
        logger.info("[CalendarPlugin] Started.")

    async def execute_tool(self, tool_name: str, payload: dict):
        if tool_name == "create_calendar_event":
            logger.info(f"[CalendarPlugin] Creating event: {payload}")
            try:
                from sqlalchemy import select
                async with db_manager.session() as db:
                    user_id = payload.get("user_id")
                    if not user_id:
                        user_stmt = select(User).limit(1)
                        user_res = await db.execute(user_stmt)
                        user = user_res.scalar_one_or_none()
                        if user:
                            user_id = user.id

                    start_time_str = payload.get("start_time")
                    end_time_str = payload.get("end_time")

                    start_dt = dateutil.parser.parse(start_time_str)
                    end_dt = dateutil.parser.parse(end_time_str)

                    # LLM often hallucinate 'Z' or +00:00 while outputting local time digits.
                    # We strip any tzinfo to force it to be evaluated as Local Time
                    start_dt = start_dt.replace(tzinfo=None)
                    end_dt = end_dt.replace(tzinfo=None)

                    local_tz = datetime.now().astimezone().tzinfo

                    start_dt = start_dt.replace(tzinfo=local_tz).astimezone(timezone.utc).replace(tzinfo=None)
                    end_dt = end_dt.replace(tzinfo=local_tz).astimezone(timezone.utc).replace(tzinfo=None)

                    new_event = CalendarEvent(
                        user_id=user_id,
                        title=payload.get("title", "No title"),
                        start_time=start_dt,
                        end_time=end_dt,
                        location=payload.get("location", ""),
                        source_origin="agent_calendar"
                    )
                    db.add(new_event)
                    await db.commit()
                    
                    if self.bus:
                        await self.bus.publish({
                            "type": "Calendar.EventCreated",
                            "payload": {"id": new_event.id, "title": new_event.title}
                        })
                        
                return {"status": "Success", "message": f"Successfully created event: {new_event.title}."}
            except Exception as e:
                logger.error(f"Error creating event: {e}")
                return {"status": "Error", "message": f"{str(e)}."}

        elif tool_name == "get_calendar_events":
            logger.info(f"[CalendarPlugin] Getting events: {payload}")
            try:
                from sqlalchemy import select
                
                async with db_manager.session() as db:
                    user_id = payload.get("user_id")
                    if not user_id:
                        user_stmt = select(User).limit(1)
                        user_res = await db.execute(user_stmt)
                        user = user_res.scalar_one_or_none()
                        if user:
                            user_id = user.id

                    start_time_str = payload.get("start_time")
                    end_time_str = payload.get("end_time")
                    
                    start_dt = dateutil.parser.parse(start_time_str)
                    end_dt = dateutil.parser.parse(end_time_str)
                    
                    local_tz = datetime.now().astimezone().tzinfo
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=local_tz)
                    start_dt = start_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=local_tz)
                    end_dt = end_dt.astimezone(timezone.utc).replace(tzinfo=None)

                    stmt = select(CalendarEvent).where(
                        CalendarEvent.user_id == user_id,
                        CalendarEvent.start_time >= start_dt,
                        CalendarEvent.start_time <= end_dt,
                        CalendarEvent.is_deleted == False
                    ).order_by(CalendarEvent.start_time.asc())
                    
                    result = await db.execute(stmt)
                    events = result.scalars().all()
                    
                    if not events:
                        return {"status": "Success", "message": "No events found in this time range."}
                    
                    events_list = []
                    for e in events:
                        local_start = e.start_time.replace(tzinfo=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
                        events_list.append(f"[{local_start}] {e.title}")
                        
                    return {"status": "Success", "events": events_list}
            except Exception as e:
                logger.error(f"Error getting events: {e}")
                return {"status": "Error", "message": f"{str(e)}"}

        elif tool_name == "clear_calendar_events":
            logger.info(f"[CalendarPlugin] Clearing all events: {payload}")
            try:
                from sqlalchemy import update
                
                async with db_manager.session() as db:
                    user_id = payload.get("user_id")
                    if not user_id:
                        from sqlalchemy import select
                        user_stmt = select(User).limit(1)
                        user_res = await db.execute(user_stmt)
                        user = user_res.scalar_one_or_none()
                        if user:
                            user_id = user.id

                    if user_id:
                        stmt = update(CalendarEvent).where(
                            CalendarEvent.user_id == user_id,
                            CalendarEvent.is_deleted == False
                        ).values(is_deleted=True)
                        await db.execute(stmt)
                        await db.commit()
                        return {"status": "Success", "message": "Successfully cleared all calendar events."}
                    else:
                        return {"status": "Error", "message": "No user found to clear events."}
            except Exception as e:
                logger.error(f"Error clearing events: {e}")
                return {"status": "Error", "message": f"{str(e)}"}

        elif tool_name == "update_calendar_event":
            logger.info(f"[CalendarPlugin] Updating event: {payload}")
            try:
                from sqlalchemy import select
                async with db_manager.session() as db:
                    user_id = payload.get("user_id")
                    if not user_id:
                        user_stmt = select(User).limit(1)
                        user_res = await db.execute(user_stmt)
                        user = user_res.scalar_one_or_none()
                        if user: user_id = user.id

                    title_kw = payload.get("title_keyword", "").lower()
                    new_start_str = payload.get("new_start_time")
                    
                    new_dt = dateutil.parser.parse(new_start_str)
                    local_tz = datetime.now().astimezone().tzinfo
                    if new_dt.tzinfo is None:
                        new_dt = new_dt.replace(tzinfo=local_tz)
                    new_dt = new_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    
                    stmt = select(CalendarEvent).where(
                        CalendarEvent.user_id == user_id,
                        CalendarEvent.is_deleted == False,
                        CalendarEvent.title.ilike(f"%{title_kw}%")
                    ).order_by(CalendarEvent.start_time.desc()).limit(1)
                    
                    res = await db.execute(stmt)
                    event = res.scalar_one_or_none()
                    
                    if not event:
                        return {"status": "Error", "message": f"No event found matching keyword: {title_kw}"}
                        
                    from datetime import timedelta
                    event.start_time = new_dt
                    event.end_time = new_dt + timedelta(hours=1)
                    await db.commit()
                    
                    return {"status": "Success", "message": f"Successfully rescheduled event '{event.title}'."}
            except Exception as e:
                logger.error(f"Error updating event: {e}")
                return {"status": "Error", "message": f"{str(e)}"}

        elif tool_name == "delete_calendar_event":
            logger.info(f"[CalendarPlugin] Deleting event: {payload}")
            try:
                from sqlalchemy import select
                async with db_manager.session() as db:
                    user_id = payload.get("user_id")
                    if not user_id:
                        user_stmt = select(User).limit(1)
                        user_res = await db.execute(user_stmt)
                        user = user_res.scalar_one_or_none()
                        if user: user_id = user.id

                    title_kw = payload.get("title_keyword", "").lower()
                    
                    stmt = select(CalendarEvent).where(
                        CalendarEvent.user_id == user_id,
                        CalendarEvent.is_deleted == False,
                        CalendarEvent.title.ilike(f"%{title_kw}%")
                    )
                    
                    res = await db.execute(stmt)
                    events = res.scalars().all()
                    
                    if not events:
                        return {"status": "Error", "message": f"No events found matching keyword: {title_kw}"}
                        
                    for e in events:
                        e.is_deleted = True
                    await db.commit()
                    
                    return {"status": "Success", "message": f"Successfully deleted {len(events)} event(s) matching keyword '{title_kw}'."}
            except Exception as e:
                logger.error(f"Error deleting event: {e}")
                return {"status": "Error", "message": f"{str(e)}"}

        raise ValueError(f"Unknown tool {tool_name}")
    async def on_stop(self):
        self.is_running = False
        logger.info("[CalendarPlugin] Stopped.")
