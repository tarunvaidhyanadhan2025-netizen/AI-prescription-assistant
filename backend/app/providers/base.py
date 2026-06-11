"""
Provider abstraction. Services depend ONLY on BaseLLMProvider.
No provider-specific logic leaks into business logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    tokens_used: int = 0


class BaseLLMProvider(ABC):
    """
    Minimal interface every LLM provider must implement.
    Two methods: complete() for text generation, embed() for embeddings.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return list of embedding vectors, one per input text."""
        ...

    @abstractmethod
    async def health_check(self) -> bool: ...
