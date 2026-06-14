from backend.domain.interfaces.event_bus import IEventBus
from backend.application.dtos.core_dtos import ToolResultDTO
from backend.infrastructure.plugins.manager import PluginManager

class ToolExecutor:
    def __init__(self, plugin_manager: PluginManager):
        self._plugin_manager = plugin_manager

    async def execute_tool(self, tool_name: str, params: dict) -> ToolResultDTO:
        try:
            result = await self._plugin_manager.execute_tool(tool_name, params)
            return ToolResultDTO(
                tool_name=tool_name,
                is_success=True,
                result_data=result
            )
        except Exception as e:
            return ToolResultDTO(
                tool_name=tool_name,
                is_success=False,
                result_data=None,
                error_message=str(e)
            )
