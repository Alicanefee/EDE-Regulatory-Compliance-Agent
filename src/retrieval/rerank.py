"""
Rerank (Cohere Rerank v3 wrapper)
================================

Cohere Rerank v3 wrapper for precision-boosting on top of vector retrieval.

Two variants:
- rerank-english-v3.0: English-only queries
- rerank-multilingual-v3.0: Arabic/English/mixed queries

For UAE EDE — use multilingual by default (Arabic + English mixed queries).
"""
from __future__ import annotations

import os
from typing import Any


class CohereReranker:
    """Cohere Rerank v3 wrapper.

    Default model: rerank-multilingual-v3.0 (handles Arabic + English)
    """

    DEFAULT_MODEL = "rerank-multilingual-v3.0"  # for UAE EDE (Arabic + English)
    ENGLISH_MODEL = "rerank-english-v3.0"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "COHERE_API_KEY not set. Get one at https://cohere.com"
            )
        self._client = None

    @property
    def client(self):
        """Lazy-init Cohere client."""
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError("cohere not installed. Install: pip install cohere")
        return self._client

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
        model: str | None = None,
    ) -> list[dict]:
        """Rerank candidate documents against a query.

        Args:
            query: The search query
            documents: List of candidate document texts
            top_n: Number of top results to return
            model: rerank-multilingual-v3.0 (default) or rerank-english-v3.0

        Returns: List of {index, relevance_score, document} sorted by score.
        """
        if model is None:
            # Auto-select based on query language
            model = self._select_model(query)

        try:
            response = self.client.rerank(
                model=model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
            )
            return [
                {
                    "index": r.index,
                    "relevance_score": r.relevance_score,
                    "document": documents[r.index],
                }
                for r in response.results
            ]
        except Exception as e:
            # On error, return documents in original order with score=0.5
            return [
                {"index": i, "relevance_score": 0.5, "document": doc}
                for i, doc in enumerate(documents[:top_n])
            ]

    def _select_model(self, query: str) -> str:
        """Auto-select model based on query language.

        If query has Arabic chars → multilingual
        Otherwise → english
        """
        has_arabic = any("\u0600" <= c <= "\u06FF" for c in query)
        return self.DEFAULT_MODEL if has_arabic else self.ENGLISH_MODEL


# Fallback: simple cosine similarity reranker (for testing without Cohere API)
class SimpleReranker:
    """Cosine similarity reranker (fallback for tests).

    NOT for production — real rerank uses a dedicated cross-encoder model.
    """

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int = 5,
        model: str | None = None,
    ) -> list[dict]:
        """Rerank using simple word overlap (Jaccard similarity)."""
        query_words = set(query.lower().split())
        scored = []
        for i, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            if not query_words or not doc_words:
                score = 0.0
            else:
                # Jaccard similarity
                intersection = len(query_words & doc_words)
                union = len(query_words | doc_words)
                score = intersection / union if union else 0.0
            scored.append({"index": i, "relevance_score": score, "document": doc})

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_n]


# Factory
def get_reranker(use_simple: bool = False) -> Any:
    """Get a reranker instance.

    Args:
        use_simple: If True, use SimpleReranker (for tests).

    Returns: Reranker with rerank() method.
    """
    if use_simple:
        return SimpleReranker()
    try:
        return CohereReranker()
    except (ValueError, ImportError):
        return SimpleReranker()
