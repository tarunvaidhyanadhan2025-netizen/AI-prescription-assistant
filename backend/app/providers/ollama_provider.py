"""Ollama provider — local LLM server via HTTP API."""
from __future__ import annotations

import json
from typing import List, Optional

import httpx

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self._base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self._model = settings.MODEL_NAME or "llama3.2"
        self._timeout = 120.0

    @property
    def name(self) -> str:
        return "ollama"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        temp = temperature if temperature is not None else settings.MODEL_TEMPERATURE

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": temp},
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        return LLMResponse(content=content, provider=self.name, model=self._model)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Use Ollama /api/embed endpoint."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": self._model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()

        # Ollama returns {"embeddings": [[...]]}
        return data.get("embeddings", [[] for _ in texts])

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
