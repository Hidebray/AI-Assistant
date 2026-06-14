from typing import List
from ..interfaces.repository import IRepository
from pydantic import BaseModel

class MemoryDTO(BaseModel):
    id: str
    content: str
    weight: float

class MemoryAggregate:
    def __init__(self, repository: IRepository):
        self._repo = repository

    async def store_memory(self, memory: MemoryDTO) -> None:
        await self._repo.save(memory)

    async def retrieve_relevant_context(self, query: str) -> List[MemoryDTO]:
        return await self._repo.find_all({"query": query})
