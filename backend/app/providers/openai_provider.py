"""OpenAI provider — GPT models + text-embedding-3-*"""
from __future__ import annotations

from typing import List, Optional

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
        self._model = settings.MODEL_NAME or "gpt-4o-mini"
        self._embed_model = settings.OPENAI_EMBEDDING_MODEL

    @property
    def name(self) -> str:
        return "openai"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        temp = temperature if temperature is not None else settings.MODEL_TEMPERATURE
        mtok = max_tokens or settings.MODEL_MAX_TOKENS

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temp,
            max_tokens=mtok,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return LLMResponse(content=content, provider=self.name, model=self._model, tokens_used=tokens)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        response = await self._client.embeddings.create(
            model=self._embed_model,
            input=[t.strip() for t in texts],
        )
        return [item.embedding for item in response.data]

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
