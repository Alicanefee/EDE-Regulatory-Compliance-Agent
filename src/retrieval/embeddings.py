"""
Embeddings (BGE-M3 fixed schema)
================================

Fixed embedding model: BGE-M3 (multilingual, 1024 dimensions).

CRITICAL (see docs/architecture.md — fixed vector schema):
- Vector model and size are FIXED.
- If model changes → all documents must be re-indexed.
"""
from __future__ import annotations

from typing import Any


MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
NORMALIZATION = "L2"
MAX_CHUNK_TOKENS = 512
OVERLAP_TOKENS = 50


class BGEEmbedder:
    """BGE-M3 embedder with fixed schema.

    All outputs MUST be 1024-dimensional L2-normalized vectors.

    Lazy-loads the model on first use (heavy import).
    """

    _instance = None  # singleton

    def __new__(cls) -> "BGEEmbedder":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    @property
    def model(self):
        """Lazy-load the BGE-M3 model."""
        if self._model is None:
            try:
                from FlagEmbedding import BGEM3FlagModel
                self._model = BGEM3FlagModel(MODEL_NAME, use_fp16=True)
            except ImportError:
                try:
                    # Fallback: sentence-transformers
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(MODEL_NAME)
                    self._is_sentence_transformers = True
                except ImportError:
                    raise ImportError(
                        "Neither FlagEmbedding nor sentence-transformers installed. "
                        "Install: pip install FlagEmbedding OR pip install sentence-transformers"
                    )
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed documents for indexing.

        Returns 1024-dim L2-normalized vectors.
        """
        if hasattr(self, "_is_sentence_transformers") and self._is_sentence_transformers:
            embeddings = self.model.encode(texts, normalize_embeddings=True)
        else:
            # BGE-M3 via FlagEmbedding
            result = self.model.encode(
                texts,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            embeddings = result["dense_vecs"]

        # Verify schema
        if not self.verify_schema(embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings):
            raise RuntimeError(
                f"Embedding schema violation. Expected {EMBEDDING_DIM} dims, "
                f"got {len(embeddings[0]) if embeddings else 0}"
            )

        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    def embed_query(self, query: str) -> list[float]:
        """Embed a search query.

        Returns 1024-dim L2-normalized vector.
        """
        if hasattr(self, "_is_sentence_transformers") and self._is_sentence_transformers:
            emb = self.model.encode([query], normalize_embeddings=True)
            return emb[0].tolist() if hasattr(emb[0], "tolist") else list(emb[0])
        else:
            result = self.model.encode(
                [query],
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
            vec = result["dense_vecs"][0]
            return vec.tolist() if hasattr(vec, "tolist") else list(vec)

    def verify_schema(self, embeddings: list[list[float]]) -> bool:
        """Verify embeddings match the fixed schema (dim + L2 normalization)."""
        for emb in embeddings:
            if len(emb) != EMBEDDING_DIM:
                return False
            # L2 norm check (should be ~1.0)
            norm = sum(x * x for x in emb) ** 0.5
            if not (0.95 <= norm <= 1.05):
                return False
        return True


# Fallback: simple hash-based embedder (for testing without BGE-M3)
class SimpleHashEmbedder:
    """Deterministic hash-based embedder for testing (NOT for production).

    Produces 1024-dim vectors by hashing the text.
    Useful for unit tests without requiring BGE-M3 weights.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.dim = dim

    def _hash_to_vector(self, text: str) -> list[float]:
        """Hash text to a 1024-dim L2-normalized vector."""
        import hashlib
        import math
        vec = [0.0] * self.dim
        for i in range(0, len(text), 4):
            chunk = text[i:i + 4]
            h = hashlib.sha256(chunk.encode()).hexdigest()
            # Use first 8 hex chars as int
            idx = int(h[:8], 16) % self.dim
            sign = 1.0 if int(h[8], 16) % 2 == 0 else -1.0
            vec[idx] += sign * 0.1
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._hash_to_vector(query)


# Factory function — returns real BGE-M3 if available, else SimpleHashEmbedder
def get_embedder(use_simple: bool = False) -> Any:
    """Get an embedder instance.

    Args:
        use_simple: If True, use SimpleHashEmbedder (for tests). If False,
                    try BGE-M3 first.

    Returns: An embedder with embed_documents() and embed_query() methods.
    """
    if use_simple:
        return SimpleHashEmbedder()
    try:
        return BGEEmbedder()
    except ImportError:
        # Fallback to simple for tests
        return SimpleHashEmbedder()
