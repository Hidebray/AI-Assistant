import logging
from typing import Dict, Any

from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus

logger = logging.getLogger(__name__)

class FlakyToolPlugin(BasePlugin):
    """
    Plugin dùng để test Agent Loop (ReAct).
    Lần đầu tiên được gọi, nó sẽ cố tình trả về Success = False.
    Lần thứ hai gọi, nó sẽ trả về Success = True.
    """

    def __init__(self):
        self.call_count = 0

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "flaky_tool_plugin",
            "version": "1.0.0",
            "description": "A tool that fails on the first try but succeeds on the second try. Used to test AI auto-correction.",
            "permissions": ["all"],
            "tools": [
                {
                    "name": "flaky_test_tool",
                    "description": "Use this tool to fetch a secret code. You must try to fetch it until you succeed.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
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
        if tool_name == "flaky_test_tool":
            self.call_count += 1
            if self.call_count == 1:
                logger.warning("FlakyTool: Intentionally failing on first try.")
                raise Exception("Temporary Server Error 503. The server is busy, please try calling this tool again.")
            else:
                logger.info("FlakyTool: Succeeding on subsequent try.")
                return {
                    "secret_code": "AAA-999"
                }
        
        return {"success": False, "message": f"Unknown tool: {tool_name}"}
