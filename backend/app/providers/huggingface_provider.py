"""
Local HuggingFace provider.
Loads a text-generation model and a sentence-transformers embedding model.
Supports 4-bit quantization via bitsandbytes.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional

from app.core.settings import settings
from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LocalHFProvider(BaseLLMProvider):
    def __init__(self):
        self._model_path = settings.HF_MODEL_PATH
        self._device = settings.HF_DEVICE
        self._load_in_4bit = settings.HF_LOAD_IN_4BIT
        self._embed_model_name = settings.EMBEDDING_MODEL
        self._pipeline = None
        self._embed_model = None
        self._loaded = False

    def _load_models(self):
        if self._loaded:
            return
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            import torch

            logger.info(f"Loading HF model: {self._model_path}")
            kwargs = {"device_map": self._device}
            if self._load_in_4bit:
                kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)

            tokenizer = AutoTokenizer.from_pretrained(self._model_path)
            model = AutoModelForCausalLM.from_pretrained(self._model_path, **kwargs)
            self._pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=settings.MODEL_MAX_TOKENS,
            )
            logger.info("HF model loaded.")
        except ImportError:
            raise RuntimeError("transformers/torch not installed.")

        try:
            from sentence_transformers import SentenceTransformer
            self._embed_model = SentenceTransformer(self._embed_model_name)
            logger.info(f"Embedding model loaded: {self._embed_model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed — embeddings unavailable.")

        self._loaded = True

    @property
    def name(self) -> str:
        return "huggingface"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        def _call():
            self._load_models()
            # Combine system + user as a single prompt (chat-template aware if tokenizer supports)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            # Try apply_chat_template; fall back to simple join
            try:
                tokenizer = self._pipeline.tokenizer
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            except Exception:
                prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}\n\n[ASSISTANT]\n"

            outputs = self._pipeline(prompt, return_full_text=False, do_sample=True,
                                     temperature=temperature or settings.MODEL_TEMPERATURE)
            return outputs[0]["generated_text"]

        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, _call)
        return LLMResponse(content=content, provider=self.name, model=self._model_path)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        def _embed():
            self._load_models()
            if self._embed_model is None:
                raise RuntimeError("Embedding model not loaded.")
            vectors = self._embed_model.encode(texts, convert_to_numpy=True)
            return [v.tolist() for v in vectors]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _embed)

    async def health_check(self) -> bool:
        try:
            self._load_models()
            return self._pipeline is not None
        except Exception as e:
            logger.warning(f"HF health check failed: {e}")
            return False
