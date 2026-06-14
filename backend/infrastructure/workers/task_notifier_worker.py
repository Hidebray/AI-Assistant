import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import Task
from backend.application.dtos.alert_dtos import Urgency
from backend.domain.events.base_events import AlertTriggeredEvent

logger = logging.getLogger(__name__)

class TaskNotifierWorker:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

    async def check_pending_tasks(self):
        try:
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            # Check for tasks due within the next 30 minutes
            target_time = now_utc + timedelta(minutes=30)

            async with db_manager.session() as db:
                stmt = select(Task).where(
                    Task.is_deleted == False,
                    Task.status != "completed",
                    Task.is_notified == False,
                    Task.deadline != None,
                    Task.deadline <= target_time
                )
                
                result = await db.execute(stmt)
                tasks = result.scalars().all()

                for task in tasks:
                    logger.info(f"[TaskNotifierWorker] Emitting alert for task: {task.title}")
                    
                    time_remaining = task.deadline - now_utc
                    minutes_left = int(time_remaining.total_seconds() / 60)
                    
                    urgency = Urgency.HIGH if minutes_left <= 15 else Urgency.MEDIUM
                    if minutes_left < 0:
                        urgency = Urgency.CRITICAL
                    
                    time_text = "đã quá hạn" if minutes_left < 0 else f"sẽ đến hạn trong {minutes_left} phút nữa"

                    alert_event = AlertTriggeredEvent(
                        source_origin="TaskNotifierWorker",
                        correlation_id="system_cron",
                        urgency_level=urgency.value.lower(),
                        alert_message=f"Công việc '{task.title}' {time_text}."
                    )
                    await self.event_bus.publish(alert_event)
                    
                    task.is_notified = True
                
                await db.commit()

        except Exception as e:
            logger.error(f"[TaskNotifierWorker] Error during execution: {e}")
