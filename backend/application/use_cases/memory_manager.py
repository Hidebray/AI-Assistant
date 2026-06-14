import tiktoken
from jinja2 import Template
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class FactExtraction(BaseModel):
    facts: list[str] = Field(description="List of factual statements or user preferences extracted from the text.")

class MemoryManager:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.max_tokens = 4000 # Configurable limit

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    async def assemble_context(
        self, 
        system_prompt_template: str, 
        user_goal: str,
        short_term_history: list[dict], 
        long_term_facts: list[str],
        adapter=None
    ) -> list[dict]:
        
        # 1. Render system prompt
        template = Template(system_prompt_template)
        formatted_facts = "\n".join([f"- {fact}" for fact in long_term_facts])
        
        system_content = template.render(
            long_term_facts=formatted_facts,
            user_goal=user_goal
        )
        
        system_msg = {"role": "system", "content": system_content}
        user_msg = {"role": "user", "content": user_goal}
        
        # 2. Token Counting & Sliding Window
        base_tokens = self.count_tokens(system_content) + self.count_tokens(user_goal)
        allowed_history_tokens = self.max_tokens * 0.8 - base_tokens
        
        final_history = []
        history_tokens = 0
        
        # Process history from newest to oldest
        messages_to_summarize = []
        for msg in reversed(short_term_history):
            msg_tokens = self.count_tokens(msg["content"])
            if history_tokens + msg_tokens <= allowed_history_tokens:
                final_history.insert(0, msg)
                history_tokens += msg_tokens
            else:
                # The rest of older messages go to summarization
                messages_to_summarize.insert(0, msg)
                
        # 3. Auto-Summarization
        summary_msg = None
        if messages_to_summarize and adapter:
            logger.info(f"Summarizing {len(messages_to_summarize)} older messages to save context space.")
            text_to_summarize = "\n".join([f"{m['role']}: {m['content']}" for m in messages_to_summarize])
            prompt = (
                "Summarize the following old conversation context into a single concise paragraph. "
                "Keep important facts. \n\n" + text_to_summarize
            )
            try:
                # LLM call to summarize
                # Using generate_stream trick or direct call if available
                # Wait, adapter has generate_response? No, adapter usually has generate_stream.
                # Let's use a simple approach: if adapter has generate_text or similar.
                # Actually, we can just use generate_stream and join.
                summary_chunks = []
                async for chunk in adapter.generate_stream([{"role": "user", "content": prompt}]):
                    summary_chunks.append(chunk)
                summary_text = "".join(summary_chunks)
                summary_msg = {"role": "system", "content": f"Summary of previous older messages: {summary_text}"}
            except Exception as e:
                logger.error(f"Auto-summarization failed: {e}")
        
        messages = [system_msg]
        if summary_msg:
            messages.append(summary_msg)
        messages.extend(final_history)
        messages.append(user_msg)
        
        return messages

    async def extract_and_store_facts(self, user_id: str, user_text: str, ai_text: str):
        """Trích xuất các facts từ cuộc hội thoại và lưu vào DB sử dụng LLM."""
        from backend.infrastructure.database.session import db_manager
        from backend.infrastructure.database.models import MemoryNode
        from backend.application.use_cases.llm_factory import LLMFactory
        
        async with db_manager.session() as db:
            adapter = await LLMFactory.get_adapter(db, user_id)
            
            prompt = (
                "Analyze the following recent message exchange and extract any factual statements, "
                "user preferences, constraints, or personal information about the user. "
                "You MUST write the extracted facts in the EXACT SAME LANGUAGE that the user used. "
                "Be specific and detailed. If there are none, return an empty list. "
                f"\n\nUser: {user_text}\nAI: {ai_text}"
            )
            
            try:
                # Trích xuất dùng Structured Output (nếu adapter hỗ trợ)
                # LLMAdapter interface has `generate_response(messages, response_format)`
                extracted: FactExtraction = await adapter.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    response_format=FactExtraction
                )
                
                if extracted and extracted.facts:
                    for fact in extracted.facts:
                        embedding = None
                        try:
                            embedding = await adapter.generate_embedding(fact)
                        except Exception as e:
                            logger.error(f"Failed to generate embedding for fact: {e}")

                        node = MemoryNode(
                            user_id=user_id,
                            context_key="preference",
                            source_origin="chat_extraction",
                            content=fact,
                            embedding=embedding,
                            weight=1.0
                        )
                        db.add(node)
                    await db.commit()
                    logger.info(f"Extracted {len(extracted.facts)} facts to memory.")
            except Exception as e:
                logger.error(f"Fact extraction failed: {e}")

    async def search_similar_facts(self, db, user_id: str, query: str, top_k: int = 5) -> list[str]:
        """Tìm kiếm facts bằng Cosine Similarity và cập nhật weight/last_accessed."""
        from backend.infrastructure.database.models import MemoryNode
        from backend.application.use_cases.llm_factory import LLMFactory
        import numpy as np
        from sqlalchemy import select
        from datetime import datetime, timezone

        try:
            stmt = select(MemoryNode).where(
                MemoryNode.user_id == user_id,
                MemoryNode.embedding.is_not(None)
            )
            result = await db.execute(stmt)
            nodes = result.scalars().all()

            if not nodes:
                stmt_fallback = select(MemoryNode).where(MemoryNode.user_id == user_id).order_by(MemoryNode.last_accessed.desc()).limit(top_k)
                res_fallback = await db.execute(stmt_fallback)
                fallback_nodes = res_fallback.scalars().all()
                for n in fallback_nodes:
                    n.last_accessed = datetime.now(timezone.utc)
                    n.weight = min(n.weight + 0.1, 100.0) # Tăng trọng số khi truy cập
                await db.commit()
                return [n.content for n in fallback_nodes]

            adapter = await LLMFactory.get_adapter(db, user_id)
            try:
                query_embedding = await adapter.generate_embedding(query)
                query_vec = np.array(query_embedding)
                
                if np.all(query_vec == 0):
                    raise Exception("Embedding generation failed (zeros returned), triggering fallback.")
                    
                scored_nodes = []
                for node in nodes:
                    node_vec = np.array(node.embedding)
                    norm_q = np.linalg.norm(query_vec)
                    norm_n = np.linalg.norm(node_vec)
                    
                    if norm_q == 0 or norm_n == 0:
                        similarity = 0.0
                    else:
                        similarity = np.dot(query_vec, node_vec) / (norm_q * norm_n)
                        
                    # Cộng thêm hệ số weight vào điểm số cuối cùng để ưu tiên các node quan trọng
                    final_score = similarity + (node.weight * 0.05)
                    scored_nodes.append((final_score, node))
                
                scored_nodes.sort(key=lambda x: x[0], reverse=True)
                top_nodes_obj = [node for score, node in scored_nodes[:top_k]]
                
                # Cập nhật last_accessed và tăng weight
                for n in top_nodes_obj:
                    n.last_accessed = datetime.now(timezone.utc)
                    n.weight = min(n.weight + 0.5, 100.0)
                contents = [n.content for n in top_nodes_obj]
                await db.commit()
                
                return contents
            except Exception as e:
                logger.error(f"Failed to search similar facts: {e}")
                
                # In-memory keyword search fallback since we can't search encrypted data in SQL
                stmt_all = select(MemoryNode).where(MemoryNode.user_id == user_id).order_by(MemoryNode.last_accessed.desc())
                res_all = await db.execute(stmt_all)
                all_nodes = res_all.scalars().all()
                
                import re
                query_clean = re.sub(r'[^\w\s]', '', query)
                keywords = [k.lower() for k in query_clean.split() if len(k) > 2]
                
                scored_nodes = []
                for n in all_nodes:
                    content_lower = n.content.lower()
                    score = sum(1 for k in keywords if k in content_lower)
                    if score > 0:
                        scored_nodes.append((score, n))
                
                if scored_nodes:
                    scored_nodes.sort(key=lambda x: x[0], reverse=True)
                    fallback_nodes = [node for score, node in scored_nodes[:top_k]]
                else:
                    fallback_nodes = all_nodes[:top_k]
                    
                for n in fallback_nodes:
                    n.last_accessed = datetime.now(timezone.utc)
                    n.weight = min(n.weight + 0.5, 100.0)
                contents = [n.content for n in fallback_nodes]
                await db.commit()
                
                return contents
        except Exception as e:
            logger.error(f"Outer exception in search_similar_facts: {e}")
            return []
