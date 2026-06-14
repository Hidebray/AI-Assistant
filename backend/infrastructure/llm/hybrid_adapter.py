import os
import logging
from typing import List, Any, Type, Optional, AsyncGenerator
from pydantic import BaseModel
from openai import AsyncOpenAI, RateLimitError, APITimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.domain.interfaces.llm_adapter import ILLMAdapter

logger = logging.getLogger("llm.hybrid")

class LLMConfig:
    def __init__(self, api_key: str, base_url: str = None, model: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @property
    def provider_name(self) -> str:
        """Human-readable provider name for logging."""
        if self.base_url and "generativelanguage.googleapis.com" in self.base_url:
            return "Google Gemini"
        if self.base_url and ("localhost" in self.base_url or "11434" in str(self.base_url)):
            return "Ollama (Local)"
        if self.base_url:
            return f"Custom ({self.base_url})"
        return "OpenAI"

class HybridLLMAdapter(ILLMAdapter):
    def __init__(self, configs: List[LLMConfig], system_prompt: str = None):
        self.configs = configs
        self.system_prompt = system_prompt or "You are AAA."
        
        self.clients = []
        for c in configs:
            if c.api_key or c.base_url:
                client = AsyncOpenAI(api_key=c.api_key or "dummy", base_url=c.base_url)
                self.clients.append((client, c.model, c.provider_name))
        
        # Log registered providers on startup
        if self.clients:
            providers = [f"{name} ({model})" for _, model, name in self.clients]
            logger.info(f"LLM Fallback Chain: {' -> '.join(providers)}")
        else:
            logger.warning("No LLM providers configured!")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError))
    )
    async def generate_response(
        self, 
        messages: List[dict], 
        response_format: Optional[Type[BaseModel]] = None
    ) -> Any:
        
        last_error = None
        for i, (client, model, provider) in enumerate(self.clients):
            try:
                logger.info(f"[{provider}] Trying model '{model}'...")
                if response_format:
                    completion = await client.beta.chat.completions.parse(
                        model=model,
                        messages=messages,
                        response_format=response_format,
                    )
                    logger.info(f"[{provider}] Response received from '{model}' (structured)")
                    return completion.choices[0].message.parsed
                else:
                    completion = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                    )
                    logger.info(f"[{provider}] Response received from '{model}'")
                    return completion.choices[0].message.content
            except Exception as e:
                logger.warning(f"[{provider}] Model '{model}' failed: {type(e).__name__}: {e}")
                last_error = e
                if i < len(self.clients) - 1:
                    next_provider = self.clients[i + 1][2]
                    logger.info(f"Falling back to {next_provider}...")
                continue
                
        logger.error("All LLM providers failed!")
        raise last_error or Exception("All LLM providers failed")

    async def generate_stream(
        self,
        messages: List[dict]
    ) -> AsyncGenerator[str, None]:
        
        last_error = None
        for i, (client, model, provider) in enumerate(self.clients):
            try:
                logger.info(f"[{provider}] Streaming from model '{model}'...")
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True
                )
                
                first_chunk = True
                async for chunk in stream:
                    content = chunk.choices[0].delta.content
                    if content is not None:
                        if first_chunk:
                            logger.info(f"[{provider}] Stream started from '{model}'")
                            first_chunk = False
                        yield content
                
                logger.info(f"[{provider}] Stream completed from '{model}'")
                return  # If successful, stop falling back
            except Exception as e:
                logger.warning(f"[{provider}] Stream from '{model}' failed: {type(e).__name__}: {e}")
                last_error = e
                if i < len(self.clients) - 1:
                    next_provider = self.clients[i + 1][2]
                    logger.info(f"🔄 Falling back to {next_provider}...")
                continue
                
        logger.error("All LLM stream providers failed!")
        raise last_error or Exception("All LLM providers failed")

    async def generate_embedding(self, text: str) -> List[float]:
        for client, model, provider in self.clients:
            try:
                embed_model = "text-embedding-3-small" if "gpt" in model else model
                logger.info(f"[{provider}] Generating embedding with '{embed_model}'...")
                response = await client.embeddings.create(
                    input=text,
                    model=embed_model
                )
                logger.info(f"[{provider}] Embedding generated")
                return response.data[0].embedding
            except Exception as e:
                # 501 means the model doesn't support embeddings, no need for scary warning
                if "501" in str(e):
                    logger.info(f"[{provider}] Model does not support embeddings (501).")
                else:
                    logger.warning(f"[{provider}] Embedding failed: {e}")
                continue
        logger.info("All embedding providers failed, returning zero vector")
        return [0.0] * 1536
