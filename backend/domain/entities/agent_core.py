"""
Domain Entity: AgentCore
========================
Đây là entity cốt lõi mô tả luồng xử lý chính của AI Agent.
Hiện tại đây là blueprint - chưa được gọi từ presentation layer.
Presentation layer đang gọi trực tiếp application/use_cases/agent_core.py.

Khi Phase 3 (Agent Intelligence) được triển khai, entity này sẽ được 
kết nối đầy đủ với DecisionEngine, Planner và ToolExecutor.
"""

from backend.domain.interfaces.event_bus import IEventBus
from backend.domain.interfaces.llm_adapter import ILLMAdapter
from backend.domain.entities.decision_engine import DecisionEngine
from backend.domain.entities.memory_aggregate import MemoryAggregate
from backend.domain.events.base_events import AgentThinkingEvent, TaskCompletedEvent
from backend.application.dtos.core_dtos import UserInputDTO, AgentResponseDTO, ContextDTO


class AgentCore:
    """
    Entity lõi điều phối toàn bộ luồng xử lý AI.
    Nhận input từ user → phân tích intent → routing → trả kết quả.
    """
    def __init__(
        self,
        event_bus: IEventBus,
        decision_engine: DecisionEngine,
    ):
        self._event_bus = event_bus
        self._decision_engine = decision_engine

    async def process_input(self, input_data: UserInputDTO) -> AgentResponseDTO:
        await self._event_bus.publish(
            AgentThinkingEvent(
                source_origin="agent_core",
                correlation_id=input_data.conversation_id,
                current_action_description="Đang phân tích ý định..."
            )
        )

        context = ContextDTO(history=[], recent_input=input_data.text)
        action = await self._decision_engine.evaluate_context(context)

        response_text = ""
        if action.action_type == "TOOL_CALL":
            response_text = f"Cần thực thi tool với payload: {action.payload}"
        elif action.action_type == "REQUIRE_CLARIFICATION":
            response_text = "Bạn có thể nói rõ hơn được không?"
        else:
            response_text = "Đã xử lý yêu cầu."

        await self._event_bus.publish(
            TaskCompletedEvent(
                source_origin="agent_core",
                correlation_id=input_data.conversation_id,
                task_id="main_task",
                is_success=True
            )
        )

        return AgentResponseDTO(
            conversation_id=input_data.conversation_id,
            response_text=response_text,
            action_taken=action.action_type
        )
