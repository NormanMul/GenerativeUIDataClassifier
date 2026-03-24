"""UDC ContextVault — Directory-recursive retrieval engine.

Implements a multi-step retrieval pipeline that navigates the virtual
filesystem hierarchy to find the most relevant context entries for a
given query.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import structlog

from udc_contextvault.core.embeddings import EmbeddingService
from udc_contextvault.storage.vector_store import ChromaDBAdapter

logger = structlog.get_logger(__name__)


class DirectoryRecursiveRetriever:
    """Retrieve relevant context entries via directory-aware vector search.

    The retrieval process follows a 5-step pipeline:

    1. **Intent analysis** — Parse the incoming query to determine target
       namespaces (resources / user / agent) and extract key phrases.
    2. **Multi-query vector search** — Generate query embedding and
       search the vector store.
    3. **Directory scoring** — Score each directory node by aggregating
       the relevance of its children.
    4. **Recursive drill-down** — Starting from the highest-scoring
       directories, recursively collect entries, pruning branches below
       a relevance threshold.
    5. **Top-K aggregation** — Merge results, de-duplicate, re-rank,
       and return the final top-K entries.
    """

    def __init__(
        self,
        vector_store: ChromaDBAdapter | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self._vector_store = vector_store or ChromaDBAdapter()
        self._embedding_service = embedding_service or EmbeddingService()

    # ------------------------------------------------------------------
    # Step 1 — Intent analysis
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_intent(query: str) -> dict[str, Any]:
        """Extract target namespace and key phrases from the query."""
        lower = query.lower()
        namespace: str | None = None
        for ns in ("resources", "user", "agent"):
            if ns in lower:
                namespace = ns
                break

        # Simple keyword extraction: longest meaningful words.
        stop = {"the", "a", "an", "is", "in", "for", "to", "of", "and", "or", "on", "with", "about"}
        words = [w for w in lower.split() if w not in stop and len(w) > 2]
        return {"namespace": namespace, "keywords": words}

    # ------------------------------------------------------------------
    # Step 2 — Vector search
    # ------------------------------------------------------------------
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        embedding = await self._embedding_service.embed_text(query)
        return self._vector_store.query(embedding=embedding, top_k=top_k, filters=filters)

    # ------------------------------------------------------------------
    # Step 3 — Directory scoring
    # ------------------------------------------------------------------
    @staticmethod
    def _score_directories(hits: list[dict[str, Any]]) -> dict[str, float]:
        """Aggregate per-entry scores to their parent directories."""
        dir_scores: dict[str, list[float]] = defaultdict(list)
        for hit in hits:
            path = hit.get("id", "")
            parts = path.rsplit("/", 1)
            parent = parts[0] if len(parts) > 1 else ""
            dir_scores[parent].append(hit.get("score", 0.0))

        return {d: sum(scores) / len(scores) for d, scores in dir_scores.items()}

    # ------------------------------------------------------------------
    # Step 4 — Recursive drill-down (filter by threshold)
    # ------------------------------------------------------------------
    @staticmethod
    def _drill_down(
        hits: list[dict[str, Any]],
        dir_scores: dict[str, float],
        threshold: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Keep entries whose directory score is above threshold."""
        valid_dirs = {d for d, s in dir_scores.items() if s >= threshold}
        return [
            h for h in hits if any(h.get("id", "").startswith(d) for d in valid_dirs) or not valid_dirs
        ]

    # ------------------------------------------------------------------
    # Step 5 — De-duplicate and rank
    # ------------------------------------------------------------------
    @staticmethod
    def _deduplicate_and_rank(hits: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for hit in sorted(hits, key=lambda h: h.get("score", 0.0), reverse=True):
            doc_id = hit.get("id", "")
            if doc_id not in seen:
                seen.add(doc_id)
                unique.append(hit)
        return unique[:top_k]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def retrieve(
        self,
        query: str,
        namespace: str | None = None,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute the 5-step retrieval pipeline."""
        # Step 1
        intent = self._parse_intent(query)
        ns = namespace or intent.get("namespace")
        logger.info("retrieval.start", query=query, namespace=ns, top_k=top_k)

        # Build metadata filter
        search_filters = dict(filters) if filters else {}
        if ns:
            search_filters["namespace"] = ns
        effective_filters = search_filters or None

        # Step 2 — vector search (fetch more than top_k to allow pruning)
        raw_hits = await self._vector_search(query, top_k=top_k * 3, filters=effective_filters)

        if not raw_hits:
            return []

        # Step 3
        dir_scores = self._score_directories(raw_hits)

        # Step 4
        pruned = self._drill_down(raw_hits, dir_scores)

        # Step 5
        results = self._deduplicate_and_rank(pruned, top_k)

        logger.info("retrieval.done", raw=len(raw_hits), pruned=len(pruned), returned=len(results))
        return results
