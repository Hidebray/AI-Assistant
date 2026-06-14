from abc import ABC, abstractmethod
from typing import List, Any, Type, Optional
from pydantic import BaseModel

class ILLMAdapter(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[dict], 
        response_format: Optional[Type[BaseModel]] = None
    ) -> Any:
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        pass
