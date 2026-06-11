"""
FallbackProvider — wraps multiple providers in a priority chain.

Tries each provider in order. Moves to the next if the current one:
  - Returns empty content
  - Raises a 429 / RESOURCE_EXHAUSTED (quota)
  - Raises any other exception

Usage (via .env):
  MODEL_PROVIDER=fallback
  FALLBACK_CHAIN=gemini:gemini-2.0-flash-lite,gemini:gemini-2.5-flash,openai:gpt-4o-mini

Each entry: <provider_name>:<model_name>
Supported provider names: gemini, openai, ollama
"""
from __future__ import annotations

import importlib
from typing import List, Optional, Tuple

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Provider registry ──────────────────────────────────────────────────────────

_PROVIDER_CLASSES = {
    "gemini":   "app.providers.gemini_provider.GeminiProvider",
    "openai":   "app.providers.openai_provider.OpenAIProvider",
    "ollama":   "app.providers.ollama_provider.OllamaProvider",
}


def _load_provider(provider_name: str, model_name: str) -> Optional[BaseLLMProvider]:
    """Instantiate a provider, overriding the model name from settings."""
    dotted = _PROVIDER_CLASSES.get(provider_name.lower())
    if not dotted:
        logger.warning(f"FallbackProvider: unknown provider '{provider_name}' — skipping")
        return None
    try:
        module_path, class_name = dotted.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)

        # Temporarily patch settings.MODEL_NAME so the provider picks up our model
        original = settings.MODEL_NAME
        settings.MODEL_NAME = model_name  # type: ignore[misc]
        try:
            instance = cls()
        finally:
            settings.MODEL_NAME = original  # type: ignore[misc]

        logger.info(f"FallbackProvider: loaded {provider_name}:{model_name}")
        return instance
    except Exception as exc:
        logger.warning(f"FallbackProvider: could not load {provider_name}:{model_name} — {exc}")
        return None


def _parse_chain(chain_str: str) -> List[Tuple[str, str]]:
    """
    Parse FALLBACK_CHAIN env var.
    Format: "gemini:gemini-2.0-flash-lite,gemini:gemini-2.5-flash,openai:gpt-4o-mini"
    """
    entries = []
    for entry in chain_str.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            provider, model = entry.split(":", 1)
            entries.append((provider.strip(), model.strip()))
        else:
            # No model specified — use provider default
            entries.append((entry.strip(), ""))
    return entries


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "resource_exhausted", "quota", "rate_limit", "rate limit"))


class FallbackProvider(BaseLLMProvider):
    """
    Tries each provider in the FALLBACK_CHAIN in order.
    On quota exhaustion or empty response, moves to the next.
    """

    def __init__(self):
        chain_str = getattr(settings, "FALLBACK_CHAIN", "")
        if not chain_str:
            raise RuntimeError(
                "MODEL_PROVIDER=fallback requires FALLBACK_CHAIN in .env.\n"
                "Example: FALLBACK_CHAIN=gemini:gemini-2.0-flash-lite,gemini:gemini-2.5-flash,openai:gpt-4o-mini"
            )

        entries = _parse_chain(chain_str)
        if not entries:
            raise RuntimeError(f"FALLBACK_CHAIN is set but could not be parsed: '{chain_str}'")

        self._providers: List[BaseLLMProvider] = []
        self._labels: List[str] = []

        for provider_name, model_name in entries:
            instance = _load_provider(provider_name, model_name)
            if instance:
                self._providers.append(instance)
                self._labels.append(f"{provider_name}:{model_name}" if model_name else provider_name)

        if not self._providers:
            raise RuntimeError(
                f"FallbackProvider: none of the providers in FALLBACK_CHAIN could be loaded.\n"
                f"Chain was: {chain_str}"
            )

        self._active_index = 0
        logger.info(f"FallbackProvider ready — chain: {self._labels}")

    @property
    def name(self) -> str:
        if self._active_index < len(self._labels):
            return self._labels[self._active_index]
        return "fallback"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        last_error: Optional[Exception] = None

        for i, (provider, label) in enumerate(zip(self._providers, self._labels)):
            try:
                logger.info(f"FallbackProvider: trying [{i+1}/{len(self._providers)}] {label}")
                response = await provider.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                if response.content and response.content.strip():
                    self._active_index = i
                    return response

                # Empty response — try next
                logger.warning(f"FallbackProvider: {label} returned empty response — trying next")

            except Exception as exc:
                last_error = exc
                if _is_quota_error(exc):
                    logger.warning(f"FallbackProvider: {label} hit quota/rate limit — trying next. ({exc})")
                else:
                    logger.warning(f"FallbackProvider: {label} failed ({type(exc).__name__}: {exc}) — trying next")

        # All providers failed
        msg = f"All providers in fallback chain exhausted: {self._labels}"
        if last_error:
            msg += f". Last error: {last_error}"
        raise RuntimeError(msg)

    async def embed(self, texts):
        for provider in self._providers:
            try:
                return await provider.embed(texts)
            except Exception:
                continue
        return [[0.0] * 384 for _ in texts]

    async def health_check(self) -> bool:
        for provider in self._providers:
            try:
                if await provider.health_check():
                    return True
            except Exception:
                continue
        return False
