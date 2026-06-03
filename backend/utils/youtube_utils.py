"""
youtube_utils.py — Helper functions for parsing and validating YouTube URLs.
"""

import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> str | None:
    """
    Extract the 11-character video ID from any standard YouTube URL format.

    Supported formats:
      - https://www.youtube.com/watch?v=VIDEO_ID
      - https://youtu.be/VIDEO_ID
      - https://youtube.com/embed/VIDEO_ID
      - https://youtube.com/shorts/VIDEO_ID
      - https://www.youtube.com/watch?v=VIDEO_ID&t=123s
    """
    url = url.strip()

    # youtu.be short links
    if "youtu.be" in url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        return match.group(1) if match else None

    # Standard watch URL
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            return qs.get("v", [None])[0]

        # /embed/ or /shorts/
        match = re.search(r"/(embed|shorts|v)/([a-zA-Z0-9_-]{11})", parsed.path)
        if match:
            return match.group(2)

    return None


def is_valid_youtube_url(url: str) -> bool:
    """Return True if the URL is a valid YouTube video URL with an extractable ID."""
    return extract_video_id(url) is not None


def build_thumbnail_url(video_id: str) -> str:
    """Return the maxresdefault thumbnail URL for a given video ID."""
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"


def build_watch_url(video_id: str) -> str:
    """Return the canonical watch URL for a given video ID."""
    return f"https://www.youtube.com/watch?v={video_id}"