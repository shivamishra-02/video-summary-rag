"""
rag_service.py — Orchestrates the full RAG pipeline.

Two public functions:
  - load_video(url)        →  index a YouTube video
  - query_video(id, query) →  answer a question about an indexed video
"""

from backend.services.transcript_service import fetch_transcript
from backend.services.chunking_service import split_transcript
from backend.services.embedding_service import embed_texts, embed_query
from backend.services import vector_store
from backend.services.gemini_service import generate_answer
from backend.models.schemas import (
    LoadVideoResponse,
    QueryResponse,
    SourceChunk,
)
from backend.config import TOP_K_RESULTS


# ── Load ───────────────────────────────────────────────────────────────────────

def load_video(url: str) -> LoadVideoResponse:
    """
    Full pipeline: URL → transcript → chunks → embeddings → FAISS index.

    If the same video is loaded again, the index is replaced.
    """
    # 1. Fetch transcript
    transcript_result = fetch_transcript(url)

    # 2. Split into chunks
    chunks = split_transcript(transcript_result.text)

    # 3. Embed all chunks
    embeddings = embed_texts(chunks)

    # 4. Store in FAISS
    vector_store.add_video(
        video_id=transcript_result.video_id,
        title=transcript_result.title,
        language=transcript_result.language,
        chunks=chunks,
        embeddings=embeddings,
    )

    return LoadVideoResponse(
        success=True,
        video_id=transcript_result.video_id,
        title=transcript_result.title,
        language=transcript_result.language,
        chunk_count=len(chunks),
        message=f"Video indexed successfully with {len(chunks)} chunks.",
    )


# ── Query ──────────────────────────────────────────────────────────────────────

def query_video(video_id: str, query: str) -> QueryResponse:
    """
    Answer a question about an already-indexed video.

    Steps:
      1. Embed the query.
      2. Search FAISS for top-k similar chunks.
      3. Check if the query is in-scope (similarity threshold).
      4. Call Gemini with the retrieved context.
      5. Return structured response.
    """
    if not vector_store.video_exists(video_id):
        raise KeyError(f"Video '{video_id}' is not indexed. Please load it first.")

    # 1. Embed query
    q_embedding = embed_query(query)

    # 2. Retrieve top-k chunks
    results = vector_store.search(video_id, q_embedding, top_k=TOP_K_RESULTS)

    # 3. Check scope
    in_scope = vector_store.is_in_scope(results)

    source_chunks = [
        SourceChunk(
            text=r["text"],
            chunk_index=r["chunk_index"],
            distance=r["distance"],
        )
        for r in results
    ]

    if not in_scope:
        return QueryResponse(
            answer="I'm sorry, I couldn't find information about that in this video.",
            video_id=video_id,
            query=query,
            source_chunks=source_chunks,
            from_video=False,
        )

    # 4. Generate answer
    context_texts = [r["text"] for r in results]
    answer = generate_answer(query, context_texts)

    # 5. Detect if Gemini itself said it couldn't answer
    out_of_scope_phrase = "couldn't find information"
    from_video = out_of_scope_phrase not in answer.lower()

    return QueryResponse(
        answer=answer,
        video_id=video_id,
        query=query,
        source_chunks=source_chunks,
        from_video=from_video,
    )