"""
schemas.py — Pydantic request/response models for all API endpoints.
"""

from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional


# ── Request Models ────────────────────────────────────────────────────────────

class LoadVideoRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        v = v.strip()
        if not any(domain in v for domain in ["youtube.com", "youtu.be"]):
            raise ValueError("URL must be a valid YouTube link")
        return v


class QueryRequest(BaseModel):
    video_id: str
    query: str

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


# ── Response Models ───────────────────────────────────────────────────────────

class LoadVideoResponse(BaseModel):
    success: bool
    video_id: str
    title: str
    language: str
    chunk_count: int
    message: str


class SourceChunk(BaseModel):
    text: str
    chunk_index: int
    distance: float


class QueryResponse(BaseModel):
    answer: str
    video_id: str
    query: str
    source_chunks: list[SourceChunk]
    from_video: bool          # False when query is out-of-scope


class VideoInfo(BaseModel):
    video_id: str
    title: str
    language: str
    chunk_count: int


class VideosListResponse(BaseModel):
    videos: list[VideoInfo]
    total: int


class DeleteResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    loaded_videos: int