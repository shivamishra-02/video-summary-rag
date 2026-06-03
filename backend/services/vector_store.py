"""
vector_store.py — In-memory FAISS vector store, one index per video.

Each video gets its own FAISS IndexFlatL2 plus a plain list of the original
chunk strings.  Everything lives in RAM; nothing is persisted to disk.
"""

import numpy as np
import faiss
from dataclasses import dataclass, field
from backend.config import TOP_K_RESULTS, SIMILARITY_THRESHOLD


@dataclass
class VideoIndex:
    """Holds the FAISS index and metadata for a single video."""
    video_id: str
    title: str
    language: str
    chunks: list[str] = field(default_factory=list)
    index: faiss.IndexFlatL2 | None = None       # type: ignore[name-defined]


# Global registry: video_id → VideoIndex
_store: dict[str, VideoIndex] = {}


# ── Write ──────────────────────────────────────────────────────────────────────

def add_video(
    video_id: str,
    title: str,
    language: str,
    chunks: list[str],
    embeddings: np.ndarray,
) -> None:
    """
    Create (or replace) the FAISS index for a video.

    Args:
        video_id:   YouTube video ID.
        title:      Human-readable video title.
        language:   Transcript language code.
        chunks:     List of raw text chunks (parallel to embeddings).
        embeddings: Float32 array of shape (n_chunks, dim).
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    _store[video_id] = VideoIndex(
        video_id=video_id,
        title=title,
        language=language,
        chunks=chunks,
        index=index,
    )


# ── Read ───────────────────────────────────────────────────────────────────────

def search(
    video_id: str,
    query_embedding: np.ndarray,
    top_k: int = TOP_K_RESULTS,
) -> list[dict]:
    """
    Return the top-k most similar chunks for a query embedding.

    Args:
        video_id:        Which video index to search.
        query_embedding: Float32 array of shape (1, dim).
        top_k:           Number of results to return.

    Returns:
        List of dicts with keys: text, chunk_index, distance.
        Empty list if video not found or all distances exceed threshold.

    Raises:
        KeyError: If video_id has not been indexed yet.
    """
    if video_id not in _store:
        raise KeyError(f"Video '{video_id}' has not been indexed. Load it first via /api/load-video.")

    entry = _store[video_id]
    actual_k = min(top_k, len(entry.chunks))

    distances, indices = entry.index.search(query_embedding, actual_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append({
            "text": entry.chunks[idx],
            "chunk_index": int(idx),
            "distance": float(dist),
        })

    return results


def is_in_scope(results: list[dict]) -> bool:
    """
    Heuristic: if the best (lowest) distance exceeds the threshold,
    the query is probably out-of-scope for this video.
    """
    if not results:
        return False
    return results[0]["distance"] <= SIMILARITY_THRESHOLD


# ── Metadata ───────────────────────────────────────────────────────────────────

def get_video_info(video_id: str) -> VideoIndex | None:
    return _store.get(video_id)


def list_videos() -> list[VideoIndex]:
    return list(_store.values())


def delete_video(video_id: str) -> bool:
    if video_id in _store:
        del _store[video_id]
        return True
    return False


def video_exists(video_id: str) -> bool:
    return video_id in _store