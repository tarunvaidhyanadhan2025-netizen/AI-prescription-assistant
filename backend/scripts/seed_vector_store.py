#!/usr/bin/env python3
"""
Seed the vector store from medicine_seed.json.
Run: python scripts/seed_vector_store.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    from app.core.settings import settings
    from app.providers.factory import get_llm_provider
    from app.services.llm_service import LLMService
    from app.services.vector_store_service import VectorStoreService

    print(f"Provider: {settings.MODEL_PROVIDER}")
    print(f"Vector DB: {settings.VECTOR_DB_ENABLED}")

    llm = LLMService(get_llm_provider())
    vs = VectorStoreService(llm)
    await vs.initialize()

    if vs._collection:
        print(f"Vector store seeded. Documents: {vs._collection.count()}")
    else:
        print("Vector store not available (disabled or ChromaDB not installed).")


if __name__ == "__main__":
    asyncio.run(main())
