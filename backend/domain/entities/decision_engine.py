from backend.domain.interfaces.llm_adapter import ILLMAdapter
from backend.application.dtos.core_dtos import ContextDTO, ActionDTO, IntentDTO


class DecisionEngine:
    """
    Domain Entity: Đánh giá context và quyết định hành động tiếp theo.
    Sử dụng LLM để phân tích intent từ input của user.
    """
    def __init__(self, llm_adapter: ILLMAdapter):
        self._llm = llm_adapter

    async def evaluate_context(self, context: ContextDTO) -> ActionDTO:
        """
        Phân tích context và trả về hành động cần thực hiện.
        Sử dụng LLM structured output để phân loại intent.
        """
        messages = [
            {"role": "system", "content": (
                "Analyze the user's input and determine their intent. "
                "Classify as CHAT (general conversation), TASK (requires tools/actions), "
                "or COMMAND (system commands)."
            )},
            {"role": "user", "content": context.recent_input}
        ]
        
        try:
            intent: IntentDTO = await self._llm.generate_response(
                messages=messages,
                response_format=IntentDTO
            )
            
            if intent.category == "TASK":
                return ActionDTO(action_type="TOOL_CALL", payload={"intent": intent.category})
            elif intent.category == "COMMAND":
                return ActionDTO(action_type="REQUIRE_CLARIFICATION", payload={})
            else:
                return ActionDTO(action_type="DIRECT_RESPONSE", payload={"intent": intent.category})
        except Exception:
            # Fallback: nếu LLM không parse được, mặc định là CHAT
            return ActionDTO(action_type="DIRECT_RESPONSE", payload={"intent": "CHAT"})
