"""
Provider factory — single import point.
Business logic never imports concrete providers.
"""
from __future__ import annotations

from functools import lru_cache

from app.core.settings import settings
from app.providers.base import BaseLLMProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROVIDERS = {
    "openai":       "app.providers.openai_provider.OpenAIProvider",
    "gemini":       "app.providers.gemini_provider.GeminiProvider",
    "ollama":       "app.providers.ollama_provider.OllamaProvider",
    "huggingface":  "app.providers.huggingface_provider.LocalHFProvider",
    "fallback":     "app.providers.fallback_provider.FallbackProvider",
    "template":     "app.providers.template_provider.TemplateProvider",
}


def _import_class(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    provider_key = settings.MODEL_PROVIDER.lower().strip()
    if provider_key not in _PROVIDERS:
        raise ValueError(
            f"Unknown MODEL_PROVIDER='{provider_key}'.\n"
            f"Valid options: {list(_PROVIDERS.keys())}\n"
            f"Check your .env file."
        )
    try:
        cls = _import_class(_PROVIDERS[provider_key])
        instance = cls()
        logger.info(f"LLM provider: {provider_key} | model: {settings.MODEL_NAME or '(default)'}")
        return instance
    except RuntimeError as e:
        raise RuntimeError(f"Failed to initialize provider '{provider_key}':\n{e}") from e
