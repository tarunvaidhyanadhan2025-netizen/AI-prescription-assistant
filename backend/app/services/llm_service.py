"""
LLMService — thin facade over BaseLLMProvider.
All services depend on this. Never on concrete providers.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    def __init__(self, provider: BaseLLMProvider):
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def is_template_mode(self) -> bool:
        return self._provider.name == "template"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return raw text content from the LLM."""
        response: LLMResponse = await self._provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Any = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """Complete and parse JSON from LLM response. Returns fallback on failure."""
        raw = await self.complete(
            system_prompt, user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self.parse_json(raw, fallback=fallback if fallback is not None else {})

    def parse_json(self, raw: str, fallback: Any = None) -> Any:
        """Parse JSON from raw LLM output. Public so callers can use it on raw completions."""
        return self._parse_json(raw, fallback=fallback)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return await self._provider.embed(texts)

    async def embed_one(self, text: str) -> List[float]:
        results = await self._provider.embed([text])
        return results[0] if results else []

    async def health_check(self) -> bool:
        return await self._provider.health_check()

    @staticmethod
    def _parse_json(raw: str, fallback: Any = None) -> Any:
        # Strip markdown code fences
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract first JSON object or array
            match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            logger.warning(f"JSON parse failed. Raw: {raw[:200]}")
            return fallback
