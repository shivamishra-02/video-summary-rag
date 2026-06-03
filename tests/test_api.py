"""
test_api.py — Integration tests for the FastAPI endpoints.
Run with:  pytest tests/test_api.py -v
Uses TestClient so no running server is needed.
Note: Gemini calls are NOT made in these tests (video loading is mocked).
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "loaded_videos" in data


class TestLoadVideoEndpoint:
    def test_invalid_url_returns_422(self):
        resp = client.post("/api/load-video", json={"url": "https://google.com"})
        assert resp.status_code == 422   # Pydantic validation error

    def test_missing_url_returns_422(self):
        resp = client.post("/api/load-video", json={})
        assert resp.status_code == 422

    @patch("backend.services.rag_service.load_video")
    def test_successful_load(self, mock_load):
        from backend.models.schemas import LoadVideoResponse
        mock_load.return_value = LoadVideoResponse(
            success=True,
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            language="en",
            chunk_count=42,
            message="Indexed 42 chunks.",
        )
        resp = client.post(
            "/api/load-video",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["video_id"] == "dQw4w9WgXcQ"
        assert data["chunk_count"] == 42


class TestQueryEndpoint:
    def test_empty_query_returns_422(self):
        resp = client.post(
            "/api/query",
            json={"video_id": "dQw4w9WgXcQ", "query": "   "},
        )
        assert resp.status_code == 422

    def test_missing_video_returns_404(self):
        resp = client.post(
            "/api/query",
            json={"video_id": "nonexistent_id", "query": "What is this about?"},
        )
        assert resp.status_code == 404

    @patch("backend.services.rag_service.query_video")
    def test_successful_query(self, mock_query):
        from backend.models.schemas import QueryResponse, SourceChunk
        mock_query.return_value = QueryResponse(
            answer="This video is about testing.",
            video_id="dQw4w9WgXcQ",
            query="What is this about?",
            source_chunks=[SourceChunk(text="test chunk", chunk_index=0, distance=0.1)],
            from_video=True,
        )
        resp = client.post(
            "/api/query",
            json={"video_id": "dQw4w9WgXcQ", "query": "What is this about?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["from_video"] is True
        assert "answer" in data


class TestVideosEndpoint:
    def test_list_videos_returns_list(self):
        resp = client.get("/api/videos")
        assert resp.status_code == 200
        data = resp.json()
        assert "videos" in data
        assert "total" in data

    def test_delete_nonexistent_returns_404(self):
        resp = client.delete("/api/videos/this_id_does_not_exist")
        assert resp.status_code == 404