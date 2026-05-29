"""
Retrieval Agent
Orchestrates RAG retrieval for medicine queries.
Combines vector similarity search with metadata filtering
and fallback web-knowledge synthesis.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.services.rag_service import RAGService, RetrievedContext
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievalAgentResult:
    """Output from the retrieval agent."""
    medicine_name: str
    context: RetrievedContext
    retrieval_strategy: str  # "vector_store" | "fallback_empty"
    num_docs_retrieved: int = 0
    top_similarity_score: float = 0.0


class RetrievalAgent:
    """
    Agent responsible for retrieving relevant medicine context
    from the ChromaDB vector store.

    Strategies:
    1. Primary: Vector similarity search for medicine name.
    2. Broadened: Retry with generic/class name if no results.
    3. Fallback: Return empty context (LLM will use parametric knowledge).
    """

    def __init__(self, rag_service: RAGService):
        self._rag = rag_service

    async def retrieve(
        self,
        medicine_name: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> RetrievedContext:
        """
        Retrieve context for a medicine name.

        Tries multiple query strategies to maximise retrieval success.
        """
        # Strategy 1: Direct medicine name
        context = await self._rag.retrieve(
            query=medicine_name,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        if not context.is_empty:
            logger.debug(f"Retrieved {len(context.documents)} docs for '{medicine_name}'")
            return context

        # Strategy 2: Append "medicine drug" to query
        broadened_query = f"{medicine_name} medicine drug pharmacology"
        context2 = await self._rag.retrieve(
            query=broadened_query,
            top_k=top_k,
            score_threshold=0.2,  # Lower threshold for broadened search
        )

        if not context2.is_empty:
            logger.debug(
                f"Broadened query retrieved {len(context2.documents)} docs for '{medicine_name}'"
            )
            return context2

        # Strategy 3: Return empty context — LLM will use its own knowledge
        logger.info(
            f"No RAG results for '{medicine_name}'. LLM will use parametric knowledge."
        )
        return RetrievedContext(query=medicine_name)

    async def retrieve_with_metadata(
        self,
        medicine_name: str,
        filters: Optional[dict] = None,
    ) -> RetrievedContext:
        """
        Retrieve with optional ChromaDB metadata filter.
        Example: filter by drug_class = "Antibiotic"
        """
        # Generate embedding via RAG service
        embedding = await self._rag._embed_query(medicine_name)

        # Query with filter
        results = await self._rag._vector_store.query(
            embedding=embedding,
            top_k=5,
            where=filters,
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        sources = [m.get("name", "Unknown") for m in metas]

        return RetrievedContext(
            query=medicine_name,
            documents=docs,
            metadatas=[m or {} for m in metas],
            distances=distances,
            sources=sources,
        )
