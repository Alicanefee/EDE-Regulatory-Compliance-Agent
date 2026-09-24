"""
Vector Store (ChromaDB persistent)
==================================

Persistent vector store using ChromaDB.

Fixed schema (see docs/architecture.md):
- Embedding model: BGE-M3 (multilingual, 1024 dim)
- Vector size: 1024
- Collections: ede_regulations, user_documents, templates, faq
- Metadata: source_type, doc_id, section, version_date, effective_date, language

CRITICAL RULE (see docs/architecture.md):
- ede_regulations is the ONLY source of regulatory rules
- user_documents is for evidence only — NEVER used as rule source
- Collections MUST NOT mix in retrieval
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


COLLECTION_EDE = "ede_regulations"
COLLECTION_USER_DOCS = "user_documents"
COLLECTION_TEMPLATES = "templates"
COLLECTION_FAQ = "faq"

ALL_COLLECTIONS = [COLLECTION_EDE, COLLECTION_USER_DOCS, COLLECTION_TEMPLATES, COLLECTION_FAQ]


class VectorStore:
    """ChromaDB persistent vector store with fixed schema."""

    def __init__(self, persist_dir: str | Path = "./data/chroma_db") -> None:
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collections = {}

    @property
    def client(self):
        """Lazy-initialize ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            except ImportError:
                raise ImportError(
                    "chromadb not installed. Install: pip install chromadb"
                )
        return self._client

    def _get_collection(self, name: str):
        """Get or create a collection."""
        if name not in ALL_COLLECTIONS:
            raise ValueError(
                f"Unknown collection: {name}. Must be one of {ALL_COLLECTIONS}"
            )
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def add_documents(
        self,
        collection: str,
        chunks: list[dict],  # each has: chunk_id, text, metadata, embedding
    ) -> None:
        """Add document chunks to a collection."""
        coll = self._get_collection(collection)
        for chunk in chunks:
            coll.add(
                ids=[chunk["chunk_id"]],
                embeddings=[chunk["embedding"]] if chunk.get("embedding") else None,
                documents=[chunk["text"]],
                metadatas=[chunk.get("metadata", {})],
            )

    def retrieve(
        self,
        collection: str,
        query_embedding: list[float] | None = None,
        query_text: str | None = None,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """Retrieve top-k chunks from a collection.

        Args:
            collection: One of COLLECTION_* constants
            query_embedding: Embedding vector for semantic search
            query_text: Text for BM25-like search (if ChromaDB supports)
            top_k: Number of results
            filter_metadata: ChromaDB metadata filter

        Returns: List of chunks with scores.
        """
        coll = self._get_collection(collection)
        kwargs = {"n_results": top_k}
        if query_embedding:
            kwargs["query_embeddings"] = [query_embedding]
        elif query_text:
            kwargs["query_texts"] = [query_text]
        else:
            raise ValueError("Must provide either query_embedding or query_text")

        if filter_metadata:
            kwargs["where"] = filter_metadata

        results = coll.query(**kwargs)
        return self._format_results(results)

    def hybrid_retrieve(
        self,
        collection: str,
        query: str,
        query_embedding: list[float] | None = None,
        top_k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[dict]:
        """Hybrid retrieval: BM25 + vector, then deduplicate.

        See docs/architecture.md (Hybrid: BM25 + vector, top_k=5).
        """
        # Vector retrieval
        if query_embedding:
            vector_results = self.retrieve(
                collection, query_embedding=query_embedding,
                top_k=top_k * 3, filter_metadata=filter_metadata,
            )
        else:
            vector_results = []

        # Text retrieval (BM25-like via ChromaDB)
        text_results = self.retrieve(
            collection, query_text=query,
            top_k=top_k * 3, filter_metadata=filter_metadata,
        )

        # Merge + deduplicate
        seen_ids = set()
        merged = []
        for r in vector_results + text_results:
            cid = r.get("chunk_id") or r.get("id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                merged.append(r)

        # Sort by score (descending) and take top_k
        merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return merged[:top_k]

    def _format_results(self, raw_results: dict) -> list[dict]:
        """Format ChromaDB results into our standard schema."""
        formatted = []
        if not raw_results or not raw_results.get("ids"):
            return formatted

        # ChromaDB returns lists of lists (one per query)
        ids_list = raw_results.get("ids", [[]])
        docs_list = raw_results.get("documents", [[]])
        metas_list = raw_results.get("metadatas", [[]])
        dists_list = raw_results.get("distances", [[]])

        # Take first query's results
        if not ids_list:
            return formatted
        ids = ids_list[0] if isinstance(ids_list[0], list) else ids_list
        docs = docs_list[0] if isinstance(docs_list[0], list) else docs_list
        metas = metas_list[0] if isinstance(metas_list[0], list) else metas_list
        dists = dists_list[0] if isinstance(dists_list[0], list) else dists_list

        for i, cid in enumerate(ids or []):
            formatted.append({
                "chunk_id": cid,
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "score": 1.0 - (dists[i] if i < len(dists) and dists[i] else 0.0),
            })

        return formatted

    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        coll = self._get_collection(collection)
        return coll.count()

    def reset_collection(self, collection: str) -> None:
        """Delete and recreate a collection (for re-indexing)."""
        if collection not in ALL_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection}")
        try:
            self.client.delete_collection(name=collection)
        except Exception:
            pass  # collection didn't exist
        if collection in self._collections:
            del self._collections[collection]
        self._get_collection(collection)  # recreate
