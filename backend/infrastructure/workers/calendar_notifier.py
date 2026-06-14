import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import CalendarEvent
from backend.domain.interfaces.event_bus import IEventBus
from backend.domain.events.base_events import SystemNewCalendarEvent

logger = logging.getLogger(__name__)

class CalendarNotifierWorker:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

    async def check_upcoming_events(self):
        """Cronjob: Kiểm tra sự kiện sắp diễn ra trong 5 phút tới và đẩy notification."""
        try:
            now = datetime.now(timezone.utc)
            # Find events that start between NOW and 5 minutes from now, and haven't been notified yet.
            upper_bound = now + timedelta(minutes=5)

            async with db_manager.session() as db:
                stmt = select(CalendarEvent).where(
                    CalendarEvent.is_deleted == False,
                    CalendarEvent.is_notified == False,
                    CalendarEvent.start_time >= now.replace(tzinfo=None),
                    CalendarEvent.start_time <= upper_bound.replace(tzinfo=None)
                )
                
                result = await db.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    # Đẩy event qua EventBus để AlertEngine xử lý
                    event_data = SystemNewCalendarEvent(
                        source_origin="calendar_notifier",
                        status="success",
                        message=f"Upcoming event: {event.title}",
                        title=event.title,
                        start_time=event.start_time.isoformat(),
                        end_time=event.end_time.isoformat(),
                        location=event.location
                    )
                    
                    logger.info(f"CalendarNotifier: Found upcoming event '{event.title}'. Pushing calendar event to EventBus.")
                    
                    await self.event_bus.publish(event_data)
                    
                    # Đánh dấu đã thông báo
                    event.is_notified = True

                if events:
                    await db.commit()

        except Exception as e:
            logger.error(f"CalendarNotifier: Error checking upcoming events: {e}")
