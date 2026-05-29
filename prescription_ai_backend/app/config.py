"""
Application Configuration
All settings loaded from environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralised application settings.
    Values are loaded from environment variables or the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "AI Prescription Explainer & Safety Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]

    # ── OpenAI ─────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = "sk-your-openai-api-key"
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.2

    # ── ChromaDB ───────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "medicines"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_USE_SERVER: bool = False   # True = remote server, False = embedded

    # ── Tesseract OCR ──────────────────────────────────────────────────────
    TESSERACT_CMD: str = "/usr/bin/tesseract"  # Override for Windows/macOS
    TESSERACT_LANG: str = "eng"
    OCR_DPI: int = 300
    OCR_SUPPORTED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"]

    # ── File Upload ────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # ── RAG ────────────────────────────────────────────────────────────────
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.4

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    LOG_FILE: str = ""   # Empty = console only

    # ── Agent ─────────────────────────────────────────────────────────────
    AGENT_MAX_ITERATIONS: int = 5
    AGENT_VERBOSE: bool = False

    # ── Multilingual ──────────────────────────────────────────────────────
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "ta", "hi", "fr", "es", "de", "zh", "ar"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def upload_dir_path(self) -> str:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


# Module-level singleton for convenient import
settings: Settings = get_settings()
