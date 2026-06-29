import logging
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import Notification, User
from sqlalchemy import select
from backend.domain.events.base_events import (
    AlertTriggeredEvent,
    SystemNewCalendarEvent,
    SystemNewEmailEvent,
    AutonomousSyncEvent
)

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

    def start(self):
        self.event_bus.subscribe("Agent.AlertTriggered", self._handle_alert_triggered)
        self.event_bus.subscribe("System.NewCalendarEvent", self._handle_new_calendar_event)
        self.event_bus.subscribe("System.NewEmail", self._handle_new_email)
        self.event_bus.subscribe("System.AutonomousSync", self._handle_auto_sync)

    async def _get_admin_user_id(self):
        async with db_manager.session() as db:
            stmt = select(User).order_by(User.created_at.asc())
            result = await db.execute(stmt)
            user = result.scalars().first()
            return user.id if user else None

    async def _create_notification(self, title: str, message: str, type: str, is_important: bool = False):
        user_id = await self._get_admin_user_id()
        if not user_id:
            logger.warning("NotificationService: No admin user found to receive notification.")
            return

        try:
            async with db_manager.session() as db:
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    type=type,
                    is_important=is_important
                )
                db.add(notification)
                await db.commit()
                logger.info(f"Notification saved to DB: {title}")
        except Exception as e:
            logger.error(f"Error saving notification to DB: {e}")

    async def _handle_alert_triggered(self, event: AlertTriggeredEvent):
        # type mapping based on urgency
        t_map = {
            "critical": "error",
            "high": "warning",
            "medium": "info",
            "low": "info"
        }
        ntype = t_map.get(event.urgency_level.lower(), "info")
        title = "Cảnh báo khẩn cấp" if ntype == "error" else "Thông báo hệ thống"
        is_important = ntype in ["error", "warning"]

        await self._create_notification(
            title=title,
            message=event.alert_message,
            type=ntype,
            is_important=is_important
        )

    async def _handle_new_calendar_event(self, event: SystemNewCalendarEvent):
        await self._create_notification(
            title="Sự kiện mới (Calendar)",
            message=f"'{event.title}' diễn ra lúc {event.start_time}",
            type="success",
            is_important=False
        )

    async def _handle_new_email(self, event: SystemNewEmailEvent):
        await self._create_notification(
            title=f"Email mới từ {event.sender}",
            message=event.subject,
            type="info",
            is_important=False
        )
        
    async def _handle_auto_sync(self, event: AutonomousSyncEvent):
        await self._create_notification(
            title="Đồng bộ tự động",
            message=event.event_title,
            type="info",
            is_important=False
        )
