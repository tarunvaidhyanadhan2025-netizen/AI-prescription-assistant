"""
RAG Service
Retrieval-Augmented Generation pipeline:
- Embeds query with OpenAI text-embedding-3-small
- Retrieves top-K documents from ChromaDB
- Returns structured context for downstream agents
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.database.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedContext:
    """Context retrieved from the vector store."""
    query: str
    documents: List[str] = field(default_factory=list)
    metadatas: List[Dict[str, Any]] = field(default_factory=list)
    distances: List[float] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def combined_text(self) -> str:
        """Concatenate all retrieved documents into a single context string."""
        if not self.documents:
            return ""
        parts = []
        for i, (doc, meta) in enumerate(zip(self.documents, self.metadatas)):
            source = meta.get("name") or meta.get("source") or f"Document {i+1}"
            parts.append(f"[Source: {source}]\n{doc}")
        return "\n\n---\n\n".join(parts)

    @property
    def is_empty(self) -> bool:
        return len(self.documents) == 0


class RAGService:
    """
    Manages the RAG retrieval pipeline:
    1. Embed the user query.
    2. Query ChromaDB for similar documents.
    3. Filter by similarity score threshold.
    4. Return RetrievedContext.
    """

    def __init__(self, vector_store: VectorStore):
        self._vector_store = vector_store
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> RetrievedContext:
        """
        Retrieve relevant medicine documents from the vector store.

        Args:
            query: The search query (medicine name or clinical question).
            top_k: Number of results to retrieve. Defaults to settings.RAG_TOP_K.
            score_threshold: Minimum similarity (0-1). Defaults to settings.RAG_SCORE_THRESHOLD.

        Returns:
            RetrievedContext with matching documents.
        """
        top_k = top_k or settings.RAG_TOP_K
        score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD

        logger.debug(f"RAG retrieve: query='{query}' top_k={top_k}")

        # Generate embedding
        try:
            embedding = await self._embed_query(query)
        except Exception as exc:
            logger.error(f"Embedding failed for query '{query}': {exc}")
            return RetrievedContext(query=query)

        # Query ChromaDB
        try:
            results = await self._vector_store.query(
                embedding=embedding,
                top_k=top_k,
            )
        except Exception as exc:
            logger.error(f"Vector store query failed: {exc}")
            return RetrievedContext(query=query)

        # Filter by score threshold (ChromaDB returns distances, not similarities)
        # Distance 0 = identical; we convert: similarity = 1 - distance (cosine)
        filtered_docs = []
        filtered_meta = []
        filtered_distances = []
        filtered_sources = []

        for doc, meta, dist in zip(
            results.get("documents", [[]])[0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0],
        ):
            similarity = max(0.0, 1.0 - dist)
            if similarity >= score_threshold:
                filtered_docs.append(doc)
                filtered_meta.append(meta or {})
                filtered_distances.append(dist)
                filtered_sources.append(
                    meta.get("name") or meta.get("source") or "Unknown"
                )

        logger.info(
            f"RAG retrieved {len(filtered_docs)}/{top_k} docs "
            f"above threshold {score_threshold} for '{query}'"
        )

        return RetrievedContext(
            query=query,
            documents=filtered_docs,
            metadatas=filtered_meta,
            distances=filtered_distances,
            sources=filtered_sources,
        )

    async def retrieve_for_multiple(
        self,
        medicines: List[str],
        top_k_per_medicine: int = 3,
    ) -> Dict[str, RetrievedContext]:
        """
        Batch retrieve for multiple medicine names.
        Returns a dict mapping medicine name -> RetrievedContext.
        """
        results: Dict[str, RetrievedContext] = {}
        for med in medicines:
            results[med] = await self.retrieve(med, top_k=top_k_per_medicine)
        return results

    # ── Internal ───────────────────────────────────────────────────────────

    async def _embed_query(self, text: str) -> List[float]:
        """Generate an OpenAI embedding for the given text."""
        response = await self._client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text.strip(),
        )
        return response.data[0].embedding
