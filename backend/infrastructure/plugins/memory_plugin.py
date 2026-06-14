import logging
from typing import Dict, Any

from sqlalchemy import delete

from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import MemoryNode

logger = logging.getLogger(__name__)

class MemoryPlugin(BasePlugin):
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "memory_plugin",
            "version": "1.0.0",
            "description": "Provides tools to manipulate the user's explicit memory.",
            "permissions": ["all"],
            "tools": [
                {
                    "name": "forget_memory",
                    "description": "Use this tool to explicitly delete a memory or fact about the user when they request to forget it.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user."
                            },
                            "context_key_or_content": {
                                "type": "string",
                                "description": "A keyword or fragment of the content you want to forget."
                            }
                        },
                        "required": ["user_id", "context_key_or_content"]
                    }
                },
                {
                    "name": "save_memory",
                    "description": "Use this tool to explicitly save a fact, preference, or important piece of information about the user to long-term memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user."
                            },
                            "fact": {
                                "type": "string",
                                "description": "The precise factual statement or preference to save. You MUST write this in the SAME LANGUAGE as the user's message. DO NOT generalize; include specific details (e.g., if user says 'I like Python programming', write 'The user likes Python programming', not just 'The user likes programming')."
                            }
                        },
                        "required": ["user_id", "fact"]
                    }
                },
                {
                    "name": "list_notes",
                    "description": "Use this tool to read the user's saved notes or memory when they ask 'What are my notes?', 'What is on my to-do list', or 'Do I have any tasks/notes'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The ID of the user."
                            }
                        },
                        "required": ["user_id"]
                    }
                }
            ]
        }

    async def on_load(self) -> None:
        pass

    async def on_start(self, event_bus: IEventBus) -> None:
        self.event_bus = event_bus

    async def on_stop(self) -> None:
        pass

    async def execute_tool(self, tool_name: str, payload: dict) -> dict:
        if tool_name == "forget_memory":
            user_id = payload.get("user_id")
            keyword = payload.get("context_key_or_content", "")
            
            if not user_id or not keyword:
                return {"success": False, "message": "Missing user_id or context_key_or_content"}

            async with db_manager.session() as db:
                # Find matching memories
                stmt = delete(MemoryNode).where(
                    MemoryNode.user_id == user_id,
                    MemoryNode.content.ilike(f"%{keyword}%")
                )
                result = await db.execute(stmt)
                await db.commit()
                
                if result.rowcount > 0:
                    return {"success": True, "message": f"Successfully deleted {result.rowcount} memory nodes matching '{keyword}'."}
                else:
                    return {"success": False, "message": f"No memories found matching '{keyword}'."}
                    
        if tool_name == "save_memory":
            user_id = payload.get("user_id")
            fact = payload.get("fact", "")
            
            if not user_id or not fact:
                return {"success": False, "message": "Missing user_id or fact"}

            from backend.application.use_cases.llm_factory import LLMFactory
            async with db_manager.session() as db:
                adapter = await LLMFactory.get_adapter(db, user_id)
                embedding = None
                try:
                    embedding = await adapter.generate_embedding(fact)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for explicit memory: {e}")
                
                node = MemoryNode(
                    user_id=user_id,
                    context_key="explicit_preference",
                    source_origin="memory_plugin",
                    content=fact,
                    embedding=embedding,
                    weight=5.0  # Higher weight for explicitly requested memories
                )
                db.add(node)
                await db.commit()
                return {"success": True, "message": f"Successfully saved fact to memory: '{fact}'"}
                
        if tool_name == "list_notes":
            user_id = payload.get("user_id")
            if not user_id:
                return {"success": False, "message": "Missing user_id"}
                
            from sqlalchemy import select
            async with db_manager.session() as db:
                stmt = select(MemoryNode).where(
                    MemoryNode.user_id == user_id,
                    MemoryNode.context_key.in_(["preference", "explicit_preference"])
                ).order_by(MemoryNode.created_at.desc()).limit(20)
                
                result = await db.execute(stmt)
                notes = result.scalars().all()
                if not notes:
                    return {"success": True, "notes": []}
                
                return {"success": True, "notes": [n.content for n in notes]}

        return {"success": False, "message": f"Unknown tool: {tool_name}"}
