"""Google Gemini provider — uses google-genai SDK."""

from __future__ import annotations

import asyncio
import re
from typing import List, Optional

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CHAT_MODEL = "gemini-2.0-flash-lite"
DEFAULT_EMBED_MODEL = "gemini-embedding-001"
_CALL_TIMEOUT = 90  # seconds per LLM call


def _parse_retry_delay(exc: Exception) -> float:
    """Extract wait time from a 429 error message, e.g. 'retry in 20.3s'."""
    match = re.search(r"retry[^0-9]*(\d+(?:\.\d+)?)\s*s", str(exc), re.IGNORECASE)
    return float(match.group(1)) if match else 5.0


class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError("google-genai not installed. Run: pip install google-genai")

        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY not set in .env. Get a free key at https://aistudio.google.com"
            )

        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._types = types
        self._model_name = settings.MODEL_NAME or DEFAULT_CHAT_MODEL
        self._embed_model = DEFAULT_EMBED_MODEL
        logger.info(f"GeminiProvider ready — model: {self._model_name}")

    @property
    def name(self) -> str:
        return "gemini"

    def _sync_call(self, system_prompt: str, user_prompt: str, temp: float, mtok: int) -> str:
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_prompt,
            config=self._types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temp,
                max_output_tokens=mtok,
            ),
        )
        return response.text or ""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        temp = temperature if temperature is not None else settings.MODEL_TEMPERATURE
        mtok = max_tokens or settings.MODEL_MAX_TOKENS
        loop = asyncio.get_event_loop()

        # Attempt 1
        try:
            content = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_call, system_prompt, user_prompt, temp, mtok),
                timeout=_CALL_TIMEOUT,
            )
            return LLMResponse(content=content, provider=self.name, model=self._model_name)
        except asyncio.TimeoutError:
            logger.warning(f"Gemini call timed out after {_CALL_TIMEOUT}s")
            return LLMResponse(content="", provider=self.name, model=self._model_name)
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                delay = _parse_retry_delay(exc)
                logger.warning(f"Gemini 429 — waiting {delay:.0f}s then retrying once")
                await asyncio.sleep(delay)
                # Attempt 2
                try:
                    content = await asyncio.wait_for(
                        loop.run_in_executor(None, self._sync_call, system_prompt, user_prompt, temp, mtok),
                        timeout=_CALL_TIMEOUT,
                    )
                    return LLMResponse(content=content, provider=self.name, model=self._model_name)
                except Exception as exc2:
                    logger.warning(f"Gemini retry also failed: {exc2}")
                    return LLMResponse(content="", provider=self.name, model=self._model_name)
            logger.warning(f"Gemini call failed: {exc}")
            return LLMResponse(content="", provider=self.name, model=self._model_name)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        def _embed_all():
            results = []
            for text in texts:
                response = self._client.models.embed_content(
                    model=self._embed_model,
                    contents=text,
                    config=self._types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                )
                results.append(response.embeddings[0].values)
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _embed_all)

    async def health_check(self) -> bool:
        try:
            def _check():
                r = self._client.models.generate_content(
                    model=self._model_name,
                    contents="Reply with just the word: ok",
                    config=self._types.GenerateContentConfig(max_output_tokens=5),
                )
                return bool(r.text)
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, _check), timeout=15
            )
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False

    async def list_available_models(self) -> List[str]:
        def _list():
            return [
                m.name.replace("models/", "")
                for m in self._client.models.list()
                if m.supported_generation_methods
                and "generateContent" in m.supported_generation_methods
            ]
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _list)
