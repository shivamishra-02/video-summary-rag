"""
main.py — FastAPI application entry point.

Endpoints:
  GET  /health                    → server health check
  POST /api/load-video            → index a YouTube video
  POST /api/query                 → query an indexed video
  GET  /api/videos                → list all loaded videos
  DELETE /api/videos/{video_id}   → remove a video from the index
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import (
    LoadVideoRequest,
    LoadVideoResponse,
    QueryRequest,
    QueryResponse,
    VideosListResponse,
    VideoInfo,
    DeleteResponse,
    HealthResponse,
)
from backend.services import rag_service, vector_store

# ── App setup ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Video Transcript RAG API",
    description="Ask questions about any YouTube video using its transcript as a knowledge base.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Streamlit frontend on any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Quick liveness check — also returns how many videos are currently indexed."""
    return HealthResponse(
        status="ok",
        loaded_videos=len(vector_store.list_videos()),
    )


@app.post("/api/load-video", response_model=LoadVideoResponse, tags=["RAG"])
def load_video(request: LoadVideoRequest):
    """
    Fetch the transcript of a YouTube video and build a FAISS index for it.
    
    - Accepts any standard YouTube URL format.
    - If the same video is loaded again, the index is refreshed.
    """
    try:
        result = rag_service.load_video(request.url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load video: {e}")


@app.post("/api/query", response_model=QueryResponse, tags=["RAG"])
def query_video(request: QueryRequest):
    """
    Ask a question about an already-indexed video.

    - Returns the answer, whether it came from the video, and source chunks.
    - If the question is unrelated to the video content, `from_video` will be False.
    """
    try:
        result = rag_service.query_video(request.video_id, request.query)
        return result
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@app.get("/api/videos", response_model=VideosListResponse, tags=["Videos"])
def list_videos():
    """List all videos currently held in memory."""
    videos = vector_store.list_videos()
    return VideosListResponse(
        videos=[
            VideoInfo(
                video_id=v.video_id,
                title=v.title,
                language=v.language,
                chunk_count=len(v.chunks),
            )
            for v in videos
        ],
        total=len(videos),
    )


@app.delete("/api/videos/{video_id}", response_model=DeleteResponse, tags=["Videos"])
def delete_video(video_id: str):
    """Remove a video's FAISS index from memory."""
    deleted = vector_store.delete_video(video_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found.")
    return DeleteResponse(success=True, message=f"Video '{video_id}' removed successfully.")


# ── Debug endpoint ────────────────────────────────────────────────────────────
@app.get("/debug/transcript-api", tags=["System"])
def debug_transcript_api():
    """Shows installed youtube-transcript-api version and available methods — helps diagnose issues."""
    try:
        import youtube_transcript_api as _yta
        from youtube_transcript_api import YouTubeTranscriptApi
        return {
            "version": getattr(_yta, "__version__", "unknown"),
            "available_methods": [m for m in dir(YouTubeTranscriptApi) if not m.startswith("_")],
        }
    except Exception as e:
        return {"error": str(e)}


# ── Dev entrypoint ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)