"""
Vector Store
High-level interface for adding and querying medicine embeddings in ChromaDB.
Uses local SentenceTransformer embeddings instead of OpenAI.
"""

import json
import os
from typing import Any, Dict, List, Optional

from sentence_transformers import SentenceTransformer

from app.database.chroma import ChromaDBClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

SEED_FILE = os.path.join(os.path.dirname(__file__), "medicine_seed.json")


class VectorStore:
    """
    Manages medicine document embeddings:
    - seed_if_empty(): loads seed data on first run
    - add_documents(): upserts documents with embeddings
    - query(): vector similarity search
    - delete(): removes documents by ID
    """

    def __init__(self, chroma_client: ChromaDBClient):
        self._chroma = chroma_client

        logger.info("Loading local embedding model...")
        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )
        logger.info("Local embedding model loaded successfully.")

    # ── Public API ─────────────────────────────────────────────────────────

    async def seed_if_empty(self):
        """
        Populate the vector store with seed medicine data if the collection is empty.
        Called once during startup.
        """
        current_count = self._chroma.count()

        if current_count > 0:
            logger.info(
                f"Vector store already has {current_count} documents. Skipping seed."
            )
            return

        logger.info("Vector store is empty. Seeding with medicine data...")

        try:
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                medicines: List[Dict[str, Any]] = json.load(f)

        except FileNotFoundError:
            logger.warning(
                f"Seed file not found at {SEED_FILE}. Creating empty store."
            )
            return

        except json.JSONDecodeError as exc:
            logger.error(f"Seed file parse error: {exc}")
            return

        docs = []
        ids = []
        metadatas = []

        for med in medicines:
            doc_text = self._medicine_to_document(med)

            doc_id = (
                f"med_{med.get('name', 'unknown').lower().replace(' ', '_')}"
            )

            meta = {
                "name": med.get("name", ""),
                "drug_class": med.get("drug_class", ""),
                "generic_name": med.get("generic_name", ""),
                "causes_drowsiness": str(
                    med.get("causes_drowsiness", False)
                ),
                "severity_level": med.get("severity_level", "low"),
                "source": "seed_database",
            }

            docs.append(doc_text)
            ids.append(doc_id)
            metadatas.append(meta)

        await self.add_documents(
            ids=ids,
            documents=docs,
            metadatas=metadatas,
        )

        logger.info(
            f"Seeded {len(docs)} medicine documents into vector store."
        )

    async def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 50,
    ):
        """
        Embed and upsert documents into ChromaDB.
        """

        metadatas = metadatas or [{} for _ in documents]

        total = len(documents)

        for start in range(0, total, batch_size):

            batch_docs = documents[start : start + batch_size]
            batch_ids = ids[start : start + batch_size]
            batch_meta = metadatas[start : start + batch_size]

            embeddings = await self._embed_batch(batch_docs)

            self._chroma.collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_meta,
            )

            logger.debug(
                f"Upserted batch {start}–{start + len(batch_docs)} of {total}"
            )

        logger.info(
            f"Added/updated {total} documents in vector store."
        )

    async def query(
        self,
        embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        """

        kwargs: Dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": min(top_k, max(1, self._chroma.count())),
            "include": ["documents", "metadatas", "distances"],
        }

        if where:
            kwargs["where"] = where

        return self._chroma.collection.query(**kwargs)

    async def query_by_text(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Convenience method: embed text then query.
        """

        embedding = await self._embed_single(query_text)

        return await self.query(
            embedding=embedding,
            top_k=top_k,
        )

    def delete(self, ids: List[str]):
        """
        Remove documents by their IDs.
        """

        self._chroma.collection.delete(ids=ids)

        logger.info(
            f"Deleted {len(ids)} documents from vector store."
        )

    def get_all_ids(self) -> List[str]:
        """
        Return all document IDs in the collection.
        """

        result = self._chroma.collection.get(include=[])

        return result.get("ids", [])

    # ── Internal ───────────────────────────────────────────────────────────

    async def _embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        """

        embedding = self.embedding_model.encode(
            text.strip() or " "
        )

        return embedding.tolist()

    async def _embed_batch(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for batch of texts.
        """

        cleaned = [
            t.strip() or " "
            for t in texts
        ]

        embeddings = self.embedding_model.encode(cleaned)

        return embeddings.tolist()

    @staticmethod
    def _medicine_to_document(med: Dict[str, Any]) -> str:
        """
        Convert a medicine JSON record to a rich text document
        suitable for semantic embedding.
        """

        name = med.get("name", "Unknown")
        generic = med.get("generic_name", "")
        drug_class = med.get("drug_class", "")
        use_case = med.get("use_case", "")
        mechanism = med.get("mechanism", "")

        side_effects = med.get("side_effects", {})

        common_se = ", ".join(
            side_effects.get("common", [])
        )

        serious_se = ", ".join(
            side_effects.get("serious", [])
        )

        dosage = med.get("common_dosages", {})

        adult_dose = dosage.get("adult", "")

        alternatives = ", ".join(
            med.get("alternatives", [])
        )

        contraindications = ", ".join(
            med.get("contraindications", [])
        )

        return (
            f"Medicine: {name} (Generic: {generic})\n"
            f"Drug Class: {drug_class}\n"
            f"Use Case: {use_case}\n"
            f"Mechanism of Action: {mechanism}\n"
            f"Common Side Effects: {common_se}\n"
            f"Serious Side Effects: {serious_se}\n"
            f"Adult Dosage: {adult_dose}\n"
            f"Contraindications: {contraindications}\n"
            f"Alternatives: {alternatives}\n"
            f"Causes Drowsiness: {med.get('causes_drowsiness', False)}\n"
        ).strip()