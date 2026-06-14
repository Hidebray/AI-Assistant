import os
from backend.domain.interfaces.llm_adapter import ILLMAdapter
from backend.domain.interfaces.event_bus import IEventBus
from backend.application.use_cases.memory_manager import MemoryManager
from backend.application.dtos.core_dtos import ActionDTO
from backend.domain.events.base_events import ToolCallRequestEvent
import uuid
import aiofiles
from jinja2 import Template

class AgentCore:
    def __init__(self, llm_adapter: ILLMAdapter, event_bus: IEventBus = None, plugin_manager = None):
        self.llm = llm_adapter
        self.event_bus = event_bus
        self.plugin_manager = plugin_manager
        self.memory = MemoryManager()
        
    async def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "../../infrastructure/prompts/core", 
            filename
        )
        try:
            async with aiofiles.open(prompt_path, "r", encoding="utf-8") as f:
                return await f.read()
        except FileNotFoundError:
            return "You are an intelligent agent."

    async def determine_action(self, text: str, short_term_history: list = None, long_term_facts: list = None, language: str = "vi") -> ActionDTO:
        prompt_raw = await self._load_prompt("react_agent.prompt.j2")
        
        available_tools = []
        if self.plugin_manager:
            available_tools = self.plugin_manager.get_available_tools()
            
        import json
        formatted_tools = json.dumps(available_tools, indent=2, ensure_ascii=False) if available_tools else "No tools available."
        
        import datetime
        current_time = datetime.datetime.now().astimezone().isoformat()
        
        template = Template(prompt_raw)
        system_prompt = template.render(
            available_tools=formatted_tools,
            current_time=current_time,
            long_term_facts=json.dumps(long_term_facts or [], ensure_ascii=False),
            system_language=language
        )

        messages = [{"role": "system", "content": system_prompt}]
        if short_term_history:
            messages.extend(short_term_history)
        messages.append({"role": "user", "content": text})
        
        try:
            action: ActionDTO = await self.llm.generate_response(
                messages=messages, 
                response_format=ActionDTO
            )
            return action
        except Exception as e:
            error_str = str(e).lower()
            if "providers failed" in error_str or "connect" in error_str:
                raise e
            print(f"Error parsing ActionDTO, fallback to DONE: {e}")
            return ActionDTO(action_type="DONE", tool_name=None, tool_arguments={})
