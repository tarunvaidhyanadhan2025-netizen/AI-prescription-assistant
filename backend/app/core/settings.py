"""
Central configuration. Everything from .env — no hardcoded values.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "Prescription OCR & Medicine Safety Platform"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept JSON array string or comma-separated string from Render env vars."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ── LLM Provider (gemini | openai | ollama | huggingface | template) ──
    MODEL_PROVIDER: str = "template"
    MODEL_NAME: str = ""
    MODEL_TEMPERATURE: float = 0.2
    MODEL_MAX_TOKENS: int = 2048

    # ── OpenAI ─────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # ── Gemini ─────────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Ollama ─────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ── HuggingFace / Local ────────────────────────────────────────────────
    HF_MODEL_PATH: str = ""          # path or HF repo id
    HF_DEVICE: str = "cpu"           # cpu | cuda | mps
    HF_LOAD_IN_4BIT: bool = False

    # ── Embeddings ─────────────────────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "local"   # openai | local
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ── OCR ────────────────────────────────────────────────────────────────
    OCR_PROVIDER: str = "tesseract"     # tesseract | easyocr
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    TESSERACT_LANG: str = "eng"

    # ── Vector DB ──────────────────────────────────────────────────────────
    VECTOR_DB_ENABLED: bool = True
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "medicines"

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prescription_db"
    DB_POOL_SIZE: int = 10
    DB_ECHO: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def parse_database_url(cls, v: str) -> str:
        """Ensure the database URL uses the asyncpg dialect for SQLAlchemy async engine."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # ── RAG ────────────────────────────────────────────────────────────────
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.4

    # ── File Upload ────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # ── Multilingual ──────────────────────────────────────────────────────
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "ta", "hi", "fr", "es", "de", "zh", "ar"]

    # ── Fallback chain (MODEL_PROVIDER=fallback) ────────────────────────────
    # Format: "provider:model,provider:model,..."
    # Example: "gemini:gemini-2.0-flash-lite,gemini:gemini-2.5-flash,openai:gpt-4o-mini"
    FALLBACK_CHAIN: str = ""

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def upload_dir_path(self) -> str:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def use_template_mode(self) -> bool:
        return self.MODEL_PROVIDER.lower() == "template"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()

