import asyncio
import logging
import traceback
from typing import Callable, Awaitable, Dict, List

from ...domain.interfaces.event_bus import IEventBus
from ...domain.interfaces.repository import IRepository
from ...domain.events.base_events import BaseEvent

logger = logging.getLogger(__name__)

class LocalEventBus(IEventBus):
    def __init__(self, repository: IRepository):
        self._subscribers: Dict[str, List[Callable[[BaseEvent], Awaitable[None]]]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._repository = repository
        self._worker_task: asyncio.Task | None = None

    def start(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from {event_type}")
            except ValueError:
                pass


    async def publish(self, event: BaseEvent) -> None:
        await self._queue.put(event)
        logger.debug(f"Event published: {event.event_type}")

    async def _worker_loop(self):
        logger.info("Event Bus worker loop started.")
        while True:
            try:
                event: BaseEvent = await self._queue.get()
                handlers = self._subscribers.get(event.event_type, [])
                
                # Dispatch to all handlers concurrently in background tasks
                for handler in handlers:
                    asyncio.create_task(self._safe_dispatch(handler, event))
                
                self._queue.task_done()
            except asyncio.CancelledError:
                logger.info("Event Bus worker loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Critical error in Event Bus worker loop: {e}")

    async def _safe_dispatch(self, handler: Callable[[BaseEvent], Awaitable[None]], event: BaseEvent):
        try:
            await handler(event)
        except Exception as e:
            error_msg = f"Handler {handler.__name__} failed for event {event.event_type}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            # Dead Letter Queue Fallback
            try:
                payload = event.model_dump_json()
                await self._repository.save_dead_letter(
                    event_type=event.event_type,
                    payload=payload,
                    error_msg=error_msg
                )
                logger.info(f"Event {event.event_id} saved to DLQ.")
            except Exception as dlq_err:
                logger.critical(f"FAILED TO SAVE TO DLQ: {dlq_err}")
