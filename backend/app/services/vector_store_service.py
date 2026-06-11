"""
VectorStoreService — handles embeddings, storage, and retrieval.
ChromaDB is optional: if VECTOR_DB_ENABLED=false, retrieval returns empty context.
Embeddings use the configured LLMService provider.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SEED_FILE = Path(__file__).parent.parent.parent / "data" / "medicine_seed.json"


@dataclass
class RetrievedContext:
    query: str
    documents: List[str] = field(default_factory=list)
    metadatas: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    distances: List[float] = field(default_factory=list)

    @property
    def combined_text(self) -> str:
        if not self.documents:
            return ""
        parts = []
        for doc, meta in zip(self.documents, self.metadatas):
            source = meta.get("name") or meta.get("source") or "Unknown"
            parts.append(f"[{source}]\n{doc}")
        return "\n\n---\n\n".join(parts)

    @property
    def is_empty(self) -> bool:
        return len(self.documents) == 0


class VectorStoreService:
    """
    Wraps ChromaDB for vector similarity search.
    If VECTOR_DB_ENABLED=false, all operations are no-ops / empty results.
    """

    def __init__(self, llm_service):
        self._llm = llm_service
        self._collection = None
        self._enabled = settings.VECTOR_DB_ENABLED

    async def initialize(self):
        if not self._enabled:
            logger.info("VectorStoreService disabled (VECTOR_DB_ENABLED=false).")
            return
        try:
            import chromadb
            client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self._collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION_NAME}' ready. "
                        f"Count: {self._collection.count()}")
            await self._seed_if_empty()
        except ImportError:
            logger.warning("chromadb not installed. Vector search disabled.")
            self._enabled = False
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}. Vector search disabled.")
            self._enabled = False

    async def _seed_if_empty(self):
        if not self._collection or self._collection.count() > 0:
            return
        if not SEED_FILE.exists():
            logger.warning(f"Seed file not found: {SEED_FILE}")
            return

        logger.info("Seeding vector store with medicine data...")
        with open(SEED_FILE, encoding="utf-8") as f:
            medicines = json.load(f)

        docs, ids, metas = [], [], []
        for med in medicines:
            doc = self._medicine_to_text(med)
            docs.append(doc)
            ids.append(f"med_{med['name'].lower().replace(' ', '_')}")
            metas.append({
                "name": med.get("name", ""),
                "drug_class": med.get("drug_class", ""),
                "generic_name": med.get("generic_name", ""),
                "severity_level": med.get("severity_level", "low"),
                "causes_drowsiness": str(med.get("causes_drowsiness", False)),
            })

        # Embed in batches of 50
        batch_size = 50
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            batch_metas = metas[i:i + batch_size]
            try:
                embeddings = await self._llm.embed(batch_docs)
                self._collection.add(
                    documents=batch_docs,
                    embeddings=embeddings,
                    ids=batch_ids,
                    metadatas=batch_metas,
                )
            except Exception as e:
                logger.error(f"Seeding batch {i//batch_size} failed: {e}")

        logger.info(f"Seeded {self._collection.count()} medicines into vector store.")

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> RetrievedContext:
        if not self._enabled or not self._collection:
            return RetrievedContext(query=query)

        top_k = top_k or settings.RAG_TOP_K
        score_threshold = score_threshold or settings.RAG_SCORE_THRESHOLD

        try:
            embedding = await self._llm.embed_one(query)
        except Exception as e:
            logger.error(f"Embedding failed for '{query}': {e}")
            return RetrievedContext(query=query)

        try:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, self._collection.count() or 1),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return RetrievedContext(query=query)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Filter by score threshold (cosine distance → similarity)
        filtered = [
            (d, m, dist) for d, m, dist in zip(docs, metas, distances)
            if (1.0 - dist) >= score_threshold
        ]

        if not filtered:
            # Retry with lower threshold
            filtered = [(d, m, dist) for d, m, dist in zip(docs, metas, distances)][:2]

        out_docs = [x[0] for x in filtered]
        out_metas = [x[1] or {} for x in filtered]
        out_dists = [x[2] for x in filtered]
        out_sources = [m.get("name", "Unknown") for m in out_metas]

        logger.debug(f"Retrieved {len(out_docs)} docs for '{query}'")
        return RetrievedContext(
            query=query,
            documents=out_docs,
            metadatas=out_metas,
            distances=out_dists,
            sources=out_sources,
        )

    @staticmethod
    def _medicine_to_text(med: dict) -> str:
        """Convert medicine dict to a searchable text document."""
        parts = [
            f"Medicine: {med.get('name', '')}",
            f"Generic: {med.get('generic_name', '')}",
            f"Class: {med.get('drug_class', '')}",
            f"Use: {med.get('use_case', '')}",
            f"Mechanism: {med.get('mechanism', '')}",
        ]
        if med.get("side_effects"):
            se = med["side_effects"]
            common = ", ".join(se.get("common", []))
            serious = ", ".join(se.get("serious", []))
            if common:
                parts.append(f"Common side effects: {common}")
            if serious:
                parts.append(f"Serious side effects: {serious}")
        if med.get("contraindications"):
            parts.append(f"Contraindications: {', '.join(med['contraindications'])}")
        if med.get("alternatives"):
            parts.append(f"Alternatives: {', '.join(med['alternatives'])}")
        if med.get("age_warnings"):
            aw = med["age_warnings"]
            for group, warn in aw.items():
                parts.append(f"{group.title()} warning: {warn}")
        return "\n".join(parts)
