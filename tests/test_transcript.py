"""
test_transcript.py — Unit tests for youtube_utils and transcript_service.
Run with:  pytest tests/test_transcript.py -v
"""

import pytest
from backend.utils.youtube_utils import extract_video_id, is_valid_youtube_url


class TestExtractVideoId:
    def test_standard_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PLxxx"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url_returns_none(self):
        assert extract_video_id("https://google.com") is None

    def test_empty_string_returns_none(self):
        assert extract_video_id("") is None


class TestIsValidYoutubeUrl:
    def test_valid_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid_url(self):
        assert is_valid_youtube_url("https://vimeo.com/12345") is False