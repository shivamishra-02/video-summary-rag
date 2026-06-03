"""
embedding_service.py — Converts text into dense vector embeddings.

Uses sentence-transformers which runs locally — no API key needed.
The model is downloaded once and cached by the library automatically.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from backend.config import EMBEDDING_MODEL

# Module-level singleton so the model is loaded only once per process
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (downloaded on first call)."""
    global _model
    if _model is None:
        print(f"[EmbeddingService] Loading model: {EMBEDDING_MODEL} (first-time download may take a minute)")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"[EmbeddingService] Model loaded ✓")
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of strings into a 2-D float32 numpy array.

    Args:
        texts: List of strings to embed.

    Returns:
        np.ndarray of shape (len(texts), embedding_dim), dtype float32.
    """
    if not texts:
        raise ValueError("Cannot embed an empty list of texts.")

    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """
    Embed a single query string.

    Returns:
        np.ndarray of shape (1, embedding_dim), dtype float32.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    return embed_texts([query.strip()])


def get_embedding_dimension() -> int:
    """Return the output dimension of the current embedding model."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()