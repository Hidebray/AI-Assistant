import asyncio
import logging
from typing import Optional, List, Dict
from sqlalchemy import select
import tiktoken

from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import User, Message, Conversation, MemoryNode
from backend.application.use_cases.llm_factory import LLMFactory
from backend.application.use_cases.agent_core import AgentCore
from backend.application.use_cases.memory_manager import MemoryManager
from backend.application.use_cases.tool_executor import ToolExecutor
from backend.domain.events.chat_events import (
    ChatRequestedEvent,
    ChatStreamChunkEvent,
    ChatStatusEvent,
    ChatDoneEvent,
    NetworkStateChangedEvent,
    ChatCancelRequestedEvent
)
from backend.application.use_cases.fallback_engine import FallbackEngine

logger = logging.getLogger(__name__)

class ChatWorker:
    def __init__(self, event_bus: IEventBus, plugin_manager):
        self.event_bus = event_bus
        self.plugin_manager = plugin_manager
        self.is_online = True
        self.fallback_engine = FallbackEngine()
        self.active_cancellations = set()

    def start(self):
        self.event_bus.subscribe("Chat.Requested", self.handle_chat_requested)
        self.event_bus.subscribe("NetworkMonitor", self.handle_network_change)
        self.event_bus.subscribe("Chat.CancelRequested", self.handle_cancel_requested)

    async def handle_cancel_requested(self, event: ChatCancelRequestedEvent):
        self.active_cancellations.add(event.client_id)

    async def handle_network_change(self, event: NetworkStateChangedEvent):
        self.is_online = event.is_online

    async def _emit_status(self, client_id: str, status: str):
        await self.event_bus.publish(ChatStatusEvent(source_origin="chat_worker", client_id=client_id, status=status))

    def _count_tokens(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> int:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = 0
        for msg in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in msg.items():
                num_tokens += len(encoding.encode(str(value)))
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    async def _summarize_context(self, adapter, db, conversation, new_messages: List[Message], old_summary: str):
        """Auto-Summarization: Nén lại các tin nhắn mới vào bản tóm tắt cũ."""
        chat_to_summarize = []
        if old_summary:
            chat_to_summarize.append({"role": "system", "content": f"Bản tóm tắt trước đó:\n{old_summary}"})
        
        for m in new_messages:
            chat_to_summarize.append({"role": m.sender_role, "content": m.content})
            
        system_prompt = "Bạn là một trợ lý thông minh. Hãy tóm tắt đoạn hội thoại dưới đây (bao gồm cả bản tóm tắt trước đó nếu có) thành một bản tóm tắt duy nhất, ngắn gọn, súc tích nhưng giữ lại đầy đủ các thông tin cốt lõi (tên riêng, ngày tháng, sở thích, trạng thái công việc)."
        messages_payload = [{"role": "system", "content": system_prompt}] + chat_to_summarize
        
        new_summary = ""
        async for chunk in adapter.generate_stream(messages=messages_payload):
            new_summary += chunk
            
        conversation.summary_content = new_summary
        conversation.last_summarized_message_id = new_messages[-1].id
        await db.commit()
        return new_summary

    async def _execute_fallback(self, content: str, user_id: str, client_id: str, language: str) -> str:
        await self._emit_status(client_id, "Executing Static Command..." if content.strip().startswith("/") else "Offline Mode...")
        fallback_response = await self.fallback_engine.process(content, user_id, language=language)
        
        for word in fallback_response.split(" "):
            if client_id in self.active_cancellations:
                logger.info(f"Fallback Generation CANCELLED for {client_id}")
                break
            chunk = word + " "
            await self.event_bus.publish(ChatStreamChunkEvent(source_origin="chat_worker", client_id=client_id, chunk=chunk))
            await asyncio.sleep(0.02)
            
        return fallback_response

    async def handle_chat_requested(self, event: ChatRequestedEvent):
        client_id = event.client_id
        user_id = event.user_id
        content = event.content
        conversation_id = event.conversation_id
        
        # Clear any previous cancellation
        self.active_cancellations.discard(client_id)
        
        try:
            async with db_manager.session() as db:
                # Lấy User
                user = await db.get(User, user_id)
                if not user:
                    await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id, error="User not found"))
                    return

                # Load Conversation
                stmt_conv = select(Conversation).where(Conversation.id == conversation_id)
                res_conv = await db.execute(stmt_conv)
                conversation = res_conv.scalar_one_or_none()
                if not conversation:
                    await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id, error="Conversation not found"))
                    return

                # Load context
                stmt_msgs = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
                res_msgs = await db.execute(stmt_msgs)
                db_messages = res_msgs.scalars().all()
                
                # Hybrid Memory Logic: Lọc ra các tin nhắn MỚI tính từ mốc last_summarized_message_id
                unsummarized_messages = []
                found_last_summarized = False
                if conversation.last_summarized_message_id:
                    for m in db_messages:
                        if found_last_summarized:
                            unsummarized_messages.append(m)
                        if m.id == conversation.last_summarized_message_id:
                            found_last_summarized = True
                    # Fallback if id was not found (e.g. deleted)
                    if not found_last_summarized:
                        unsummarized_messages = db_messages
                else:
                    unsummarized_messages = db_messages

                chat_context = [{"role": m.sender_role, "content": m.content} for m in unsummarized_messages]
                
                # Pop out the current message we are processing
                current_msg_dict = None
                if chat_context and chat_context[-1]["content"] == content and chat_context[-1]["role"] == "user":
                    current_msg_dict = chat_context.pop()
                    
                # Tính tổng Token hiện tại (kể cả phần user chuẩn bị gửi)
                context_with_summary = []
                if conversation.summary_content:
                    context_with_summary.append({"role": "system", "content": f"Summary of previous chat:\n{conversation.summary_content}"})
                context_with_summary.extend(chat_context)
                if current_msg_dict:
                    context_with_summary.append(current_msg_dict)
                    
                total_tokens = self._count_tokens(context_with_summary)
                
                if total_tokens > 3000 and len(unsummarized_messages) > 3:
                    await self._emit_status(client_id, "Compressing old memory...")
                    adapter = await LLMFactory.get_adapter(db, user_id, getattr(event, "language", "vi"))
                    # Bỏ tin nhắn hiện hành ra khỏi việc tóm tắt để tránh bị kẹt
                    msgs_to_summarize = unsummarized_messages[:-1] if unsummarized_messages[-1].content == content else unsummarized_messages
                    new_summary = await self._summarize_context(adapter, db, conversation, msgs_to_summarize, conversation.summary_content)
                    
                    # Setup lại chat_context mới tinh (chỉ có system summary + current msg)
                    chat_context = []
                    context_with_summary = [{"role": "system", "content": f"Summary of previous chat:\n{new_summary}"}]
                    if current_msg_dict:
                        context_with_summary.append(current_msg_dict)

                if content.strip().startswith("/") or not self.is_online:
                    # Offline Fallback Routing / Static Commands
                    language = getattr(event, "language", "vi")
                    full_response = await self._execute_fallback(content, user_id, client_id, language)
                    plan_metadata = None
                else:
                    # Online LLM Routing
                    facts = await MemoryManager().search_similar_facts(db, user_id, content, top_k=5)
    
                    # Initialize Agent
                    language = getattr(event, "language", "vi")
                    adapter = await LLMFactory.get_adapter(db, user_id, language)
                    agent = AgentCore(llm_adapter=adapter, plugin_manager=self.plugin_manager)
    
                    plan_metadata = None
                    full_response = ""
    
                    max_iterations = 3
                    iteration = 0
                    
                    # Context for agent including conversation history (without current message)
                    agent_context = context_with_summary[:-1] if current_msg_dict else context_with_summary
                    all_execution_results = []
                    tool_logs = []
                    called_tools = set()
                    
                    while iteration < max_iterations:
                        await self._emit_status(client_id, "Thinking...")
                        
                        current_prompt = content
                        if tool_logs:
                            current_prompt += "\n\nTool Results so far:\n" + "\n".join(tool_logs)
                            
                        action = await agent.determine_action(text=current_prompt, short_term_history=agent_context, long_term_facts=facts, language=language)
                        
                        if action.action_type == "DONE" or action.action_type == "DIRECT_RESPONSE" or not action.tool_name:
                            break
                            
                        # Deduplicate tool calls
                        if action.tool_name in called_tools:
                            logger.info(f"Skipping duplicate tool call: {action.tool_name}")
                            break
                        called_tools.add(action.tool_name)
                            
                        # It is a TOOL_CALL
                        await self._emit_status(client_id, f"Running {action.tool_name}...")
                        executor = ToolExecutor(self.plugin_manager)
                        
                        # No Plan UI Approval needed anymore
                        payload = action.tool_arguments or {}
                        payload["user_id"] = user_id
                        result = await executor.execute_tool(action.tool_name, payload)
                        all_execution_results.append(result)
                        
                        # Append result to logs
                        result_str = getattr(result, 'result_data', str(result)) if getattr(result, 'is_success', True) else getattr(result, 'error_message', 'Unknown error')
                        tool_logs.append(f"- {action.tool_name} returned: {result_str}")
                        
                        iteration += 1

                    # Stream final response
                    await self._emit_status(client_id, "Generating...")
                    final_user_content = content
                    if tool_logs:
                        final_user_content += "\n\nTool Results:\n" + "\n".join(tool_logs)
                        final_user_content += "\n\n(System: You have executed the necessary tools. Synthesize the final outcome and reply to the user based on the tool results.)"
                    report_context = agent_context + [{"role": "user", "content": final_user_content}]
                    
                    system_prompt_with_facts = adapter.system_prompt
                    if facts:
                        system_prompt_with_facts += "\n\nFacts:\n" + "\n".join([f"- {f}" for f in facts])
                        
                    messages_payload = [{"role": "system", "content": system_prompt_with_facts}] + report_context
                    logger.info(f"=== LLM MESSAGES PAYLOAD ===\n{messages_payload}")
                    try:
                        async for chunk in adapter.generate_stream(messages=messages_payload):
                            if client_id in self.active_cancellations:
                                logger.info(f"LLM Generation CANCELLED for {client_id}")
                                break
                            full_response += chunk
                            await self.event_bus.publish(ChatStreamChunkEvent(source_origin="chat_worker", client_id=client_id, chunk=chunk))
                    except Exception as e:
                        logger.error(f"LLM stream error: {e}", exc_info=True)
                        error_str = str(e).lower()
                        if "404" in error_str or "connect" in error_str or "providers failed" in error_str:
                            raise e # Re-raise for Fallback Engine to handle
                        else:
                            user_friendly_msg = f"Lỗi phản hồi từ AI: {str(e)}"
                            await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id, error=user_friendly_msg))
                            return

                # Lưu Message AI
                ai_msg = Message(
                    conversation_id=conversation_id,
                    sender_role="assistant",
                    source_origin="llm",
                    content=full_response,
                    metadata_=plan_metadata
                )
                db.add(ai_msg)
                await db.commit()

            # Async Extract Memory
            if self.is_online:
                asyncio.create_task(MemoryManager().extract_and_store_facts(user_id, content, full_response))

            await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id))

        except Exception as e:
            logger.error(f"ChatWorker Error: {e}", exc_info=True)
            error_str = str(e).lower()
            if "providers failed" in error_str or "404" in error_str or "connect" in error_str:
                logger.warning(f"LLM completely failed for {client_id}. Redirecting to Fallback Engine.")
                try:
                    language = getattr(event, "language", "vi")
                    full_response = await self._execute_fallback(content, user_id, client_id, language)
                    
                    async with db_manager.session() as db:
                        ai_msg = Message(
                            conversation_id=conversation_id,
                            sender_role="assistant",
                            source_origin="fallback",
                            content=full_response,
                        )
                        db.add(ai_msg)
                        await db.commit()
                        
                    await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id))
                    return
                except Exception as fallback_e:
                    logger.error(f"Fallback engine also failed: {fallback_e}")
                    error_msg = "Không thể kết nối đến LLM. Vui lòng cấu hình API Key trong Settings hoặc bật Local LLM (Ollama)."
            else:
                error_msg = f"Internal Error: {str(e)}"
            await self.event_bus.publish(ChatDoneEvent(source_origin="chat_worker", client_id=client_id, error=error_msg))
