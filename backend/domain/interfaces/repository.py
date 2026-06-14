from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

class IRepository(ABC):
    @abstractmethod
    async def save(self, entity: Any) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def find_all(self, criteria: Dict[str, Any]) -> List[Any]:
        pass
        
    @abstractmethod
    async def save_dead_letter(self, event_type: str, payload: str, error_msg: str) -> None:
        pass
