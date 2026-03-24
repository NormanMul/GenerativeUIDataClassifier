"""UDC ContextVault — ChromaDB vector store adapter.

Provides a thin wrapper around ChromaDB for storing and querying
context entry embeddings with metadata filtering.
"""

from __future__ import annotations

import os
from typing import Any

import chromadb
import structlog

logger = structlog.get_logger(__name__)

COLLECTION_NAME = "udc_context"


class ChromaDBAdapter:
    """Manage context embeddings in a ChromaDB collection.

    Supports add / query / delete operations against a single
    ChromaDB collection dedicated to the ContextVault.
    """

    def __init__(self) -> None:
        url = os.environ.get("CHROMADB_URL", "http://localhost:8000")
        self._client = chromadb.HttpClient(host=url.rstrip("/"))
        self._collection = self._client.get_or_create_collection(name=COLLECTION_NAME)

    def add(
        self,
        id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        content: str,
    ) -> None:
        """Insert or upsert an embedding with associated metadata."""
        # ChromaDB metadata values must be str, int, float, or bool.
        safe_meta = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
        self._collection.upsert(
            ids=[id],
            embeddings=[embedding],
            metadatas=[safe_meta],
            documents=[content],
        )
        logger.info("vector_store.add", id=id)

    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Find the nearest neighbours for a query embedding."""
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
        }
        if filters:
            kwargs["where"] = filters

        results = self._collection.query(**kwargs)

        hits: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            # ChromaDB returns L2 distance; convert to a 0-1 similarity score.
            distance = distances[i] if i < len(distances) else 0.0
            score = 1.0 / (1.0 + distance)
            hits.append(
                {
                    "id": doc_id,
                    "score": score,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "content": documents[i] if i < len(documents) else "",
                }
            )
        return hits

    def delete(self, id: str) -> None:
        """Remove an entry from the vector store."""
        self._collection.delete(ids=[id])
        logger.info("vector_store.delete", id=id)
