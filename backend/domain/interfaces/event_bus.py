from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from ..events.base_events import BaseEvent

class IEventBus(ABC):
    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        pass
