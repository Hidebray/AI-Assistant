from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from backend.application.dtos.core_dtos import ActionDTO
from backend.application.encryption import decrypt_value
from backend.infrastructure.llm.hybrid_adapter import HybridLLMAdapter

class MockLLMAdapter:
    def __init__(self, system_prompt=None):
        self.system_prompt = system_prompt
    
    async def generate_response(self, messages, response_format=None):
        if response_format == IntentDTO:
            return IntentDTO(
                category=IntentCategory.CHAT,
                confidence=1.0,
                rationale="Mock adapter default response for local development."
            )
        if response_format == PlanDTO:
            return PlanDTO(
                rationale="Mock plan for local development.",
                steps=[
                    SubTaskDTO(
                        task_name="Mock task",
                        tool_required=None,
                        dependencies=[]
                    )
                ],
                requires_user_approval=False
            )
        return "Xin chào, đây là tin nhắn phản hồi từ Mock LLM."
    
    async def generate_stream(self, messages):
        import asyncio
        response = "Xin chào, đây là tin nhắn phản hồi từ Mock LLM. Mọi tính năng giao tiếp và streaming đã hoạt động hoàn hảo!"
        for word in response.split(" "):
            yield word + " "
            await asyncio.sleep(0.1)
            
    async def generate_embedding(self, text):
        return [0.0] * 1536

class LLMFactory:
    @staticmethod
    async def get_adapter(db: AsyncSession, user_id: str, language: str = "vi"):
        from backend.infrastructure.database.models import UserSetting
        import os
        
        # Load user settings for API keys
        stmt = select(UserSetting).where(UserSetting.user_id == user_id)
        result = await db.execute(stmt)
        settings_rows = result.scalars().all()
        settings = {s.setting_key: s.setting_value for s in settings_rows}
        
        openai_key_enc = settings.get("llm.openai_key")
        openai_key = decrypt_value(openai_key_enc) if openai_key_enc else None
        
        gemini_key_enc = settings.get("llm.gemini_key")
        gemini_key = decrypt_value(gemini_key_enc) if gemini_key_enc else None
        
        local_url = settings.get("llm.ollama_url") or "http://localhost:11434"
        if not local_url.endswith("/v1") and not local_url.endswith("/v1/"):
            local_url = local_url.rstrip("/") + "/v1"
        
        # Load user-configured system prompt or use a sensible default
        user_system_prompt = settings.get("llm.system_prompt") or None
        
        if not user_system_prompt:
            if language.startswith("vi"):
                user_system_prompt = (
                    "Bạn là AAA (Autonomous AI Assistant), một trợ lý AI thông minh, thân thiện và hữu ích. "
                    "Luôn luôn phản hồi bằng ngôn ngữ mà người dùng sử dụng (chủ yếu là Tiếng Việt). "
                    "Tuyệt đối không xưng tên là LLaMA, GPT, Gemini hay bất kỳ tên mô hình nào khác. "
                    "Tên của bạn là AAA."
                )
            else:
                user_system_prompt = (
                    "You are AAA (Autonomous AI Assistant), a helpful, friendly and knowledgeable AI assistant. "
                    "Always respond in the same language the user uses. "
                    "Never identify yourself as LLaMA, GPT, Gemini, or any other model name. "
                    "You are AAA."
                )
        
        from backend.infrastructure.llm.hybrid_adapter import LLMConfig
        configs = []
        
        if openai_key and openai_key != "sk-dummy-key-for-now":
            configs.append(LLMConfig(api_key=openai_key, model="gpt-4o-mini"))
            
        if gemini_key:
            configs.append(LLMConfig(api_key=gemini_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", model="gemini-flash-latest"))
            
        # Determine which local model to use
        local_model = "llama3" # fallback
        try:
            from backend.infrastructure.llm.ollama_manager import ollama_manager
            status = await ollama_manager.check_status()
            if status.get("installed") and status.get("models"):
                models = status["models"]
                # Prefer the recommended model if installed, otherwise pick the first one
                recommended = status.get("recommended_model")
                if recommended in models:
                    local_model = recommended
                else:
                    local_model = models[0]
        except Exception:
            pass

        configs.append(LLMConfig(api_key="ollama", base_url=local_url, model=local_model))
        
        return HybridLLMAdapter(configs=configs, system_prompt=user_system_prompt)
