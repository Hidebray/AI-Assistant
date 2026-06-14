"""
Application Use Case: Planner
Nhận goal từ user, sử dụng LLM để sinh ra kế hoạch thực thi (PlanDTO).
"""
from typing import List
from backend.domain.interfaces.llm_adapter import ILLMAdapter
from backend.application.dtos.core_dtos import PlanDTO, SubTaskDTO


class Planner:
    def __init__(self, llm_adapter: ILLMAdapter):
        self._llm = llm_adapter

    async def create_plan(self, goal: str) -> PlanDTO:
        """Gọi LLM để sinh kế hoạch từ goal của user."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a planning engine. Break down the user's goal into actionable sub-tasks. "
                    "Output ONLY valid JSON matching the PlanDTO schema. Max 5 steps."
                )
            },
            {"role": "user", "content": goal}
        ]

        try:
            plan: PlanDTO = await self._llm.generate_response(
                messages=messages,
                response_format=PlanDTO
            )
            return plan
        except Exception:
            # Fallback: trả về plan đơn giản nếu LLM không parse được
            return PlanDTO(
                rationale="Auto-generated fallback plan",
                steps=[SubTaskDTO(task_name=goal, tool_required=None, dependencies=[])],
                requires_user_approval=False
            )

    async def breakdown_task(self, task: SubTaskDTO) -> List[SubTaskDTO]:
        """Phân tích một task thành các sub-task nhỏ hơn (future use)."""
        return []
