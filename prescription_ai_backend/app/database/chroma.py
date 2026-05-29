"""
ChromaDB Client
Manages ChromaDB connection (embedded or server mode),
collection creation, and health-check utilities.
"""

import os
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaDBClient:
    """
    Wraps the ChromaDB client with async-friendly interface.

    Supports two modes:
    - Embedded (default): PersistentClient backed by a local directory.
    - Server: HttpClient connected to a remote ChromaDB server.
    """

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None

    async def initialize(self):
        """
        Create the ChromaDB client and ensure the medicine collection exists.
        Called during application startup.
        """
        if settings.CHROMA_USE_SERVER:
            logger.info(
                f"Connecting to ChromaDB server at "
                f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
            )
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
        else:
            persist_dir = settings.CHROMA_PERSIST_DIR
            os.makedirs(persist_dir, exist_ok=True)
            logger.info(f"Using embedded ChromaDB at '{persist_dir}'")
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

        # Ensure collection exists
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
        logger.info(
            f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' ready. "
            f"Documents: {self._collection.count()}"
        )

    async def ping(self):
        """Raise if ChromaDB is not reachable."""
        if self._client is None:
            raise RuntimeError("ChromaDB client not initialised.")
        # heartbeat() raises on failure for HttpClient
        try:
            self._client.heartbeat()
        except AttributeError:
            # PersistentClient doesn't have heartbeat — just check collection
            if self._collection is None:
                raise RuntimeError("Collection not initialised.")

    async def close(self):
        """Cleanly close the ChromaDB connection."""
        # ChromaDB PersistentClient auto-flushes on gc; explicit close for server
        if self._client and settings.CHROMA_USE_SERVER:
            try:
                self._client.clear_system_cache()  # best-effort
            except Exception:
                pass
        logger.info("ChromaDB client closed.")

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            raise RuntimeError("ChromaDB not initialised. Call initialize() first.")
        return self._collection

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            raise RuntimeError("ChromaDB not initialised. Call initialize() first.")
        return self._client

    def reset(self):
        """
        Drop and recreate the collection.
        ⚠ Destructive — for testing/seeding only.
        """
        if self._client:
            self._client.delete_collection(settings.CHROMA_COLLECTION_NAME)
            self._collection = self._client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.warning(f"Collection '{settings.CHROMA_COLLECTION_NAME}' reset.")

    def count(self) -> int:
        """Return the number of documents in the collection."""
        return self._collection.count() if self._collection else 0
