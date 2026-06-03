"""
transcript_service.py — Fetches the transcript of a YouTube video.

Handles the youtube-transcript-api v0.6.x API where:
- FetchedTranscript objects use attribute access (.text, .start, .duration)
  NOT dict access (["text"]) in newer versions
- list_transcripts() can fail with XML errors if YouTube blocks the request
- Falls back to direct fetch() as a simpler path
"""

import requests as _requests
from backend.utils.youtube_utils import extract_video_id


class TranscriptResult:
    """Holds the raw transcript text plus metadata."""
    def __init__(self, video_id: str, text: str, language: str, title: str = ""):
        self.video_id = video_id
        self.text = text
        self.language = language
        self.title = title


def _segments_to_text(segments) -> str:
    """
    Convert transcript segments to plain text.
    Handles BOTH dict-style (old API) and object-style (new API) segments.
    """
    parts = []
    for seg in segments:
        if isinstance(seg, dict):
            parts.append(seg.get("text", "").strip())
        else:
            # FetchedTranscriptSnippet object (youtube-transcript-api >= 0.6.3)
            parts.append(getattr(seg, "text", str(seg)).strip())
    return " ".join(p for p in parts if p).replace("\n", " ").strip()


def fetch_transcript(url: str, preferred_language: str = "en") -> TranscriptResult:
    """
    Given a YouTube URL, return a TranscriptResult.

    Strategy (most reliable → least):
      1. Direct get_transcript() — simplest, avoids list_transcripts XML issue
      2. list_transcripts() with language fallback
      3. Raise a clear error
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract a valid video ID from URL: {url}")

    # Lazy import so errors are caught per-call
    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi,
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )
    except ImportError:
        raise RuntimeError("youtube-transcript-api is not installed. Run: pip install youtube-transcript-api")

    last_error = None

    # ── Strategy 1: direct get_transcript (fastest, avoids XML list call) ──────
    for lang in [preferred_language, "en", None]:
        try:
            if lang is None:
                # No language filter — let YouTube pick
                segments = YouTubeTranscriptApi.get_transcript(video_id)
            else:
                segments = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            
            text = _segments_to_text(segments)
            if text:
                used_lang = lang or "auto"
                title = _get_video_title(video_id)
                return TranscriptResult(video_id=video_id, text=text, language=used_lang, title=title)
        except (NoTranscriptFound, Exception) as e:
            last_error = e
            continue

    # ── Strategy 2: list_transcripts() with full fallback ─────────────────────
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        used_language = preferred_language

        # Try manual transcripts first (higher quality)
        try:
            transcript = transcript_list.find_manually_created_transcript([preferred_language, "en"])
            used_language = transcript.language_code
        except Exception:
            pass

        # Then auto-generated
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript([preferred_language, "en"])
                used_language = transcript.language_code + " (auto)"
            except Exception:
                pass

        # Then whatever is available
        if transcript is None:
            available = list(transcript_list)
            if available:
                transcript = available[0]
                used_language = transcript.language_code

        if transcript is not None:
            segments = transcript.fetch()
            text = _segments_to_text(segments)
            if text:
                title = _get_video_title(video_id)
                return TranscriptResult(video_id=video_id, text=text, language=used_language, title=title)

    except VideoUnavailable:
        raise ValueError(f"Video '{video_id}' is unavailable or private.")
    except TranscriptsDisabled:
        raise ValueError(
            f"Transcripts/captions are disabled for this video ('{video_id}'). "
            "Try a different video that has captions enabled."
        )
    except Exception as e:
        last_error = e

    # ── All strategies failed ─────────────────────────────────────────────────
    raise ValueError(
        f"Could not fetch transcript for video '{video_id}'. "
        f"Possible reasons: video has no captions, is age-restricted, or is private. "
        f"Last error: {last_error}"
    )


def _get_video_title(video_id: str) -> str:
    """
    Get video title via YouTube's public oEmbed endpoint (no API key needed).
    Falls back to the video ID string if anything fails.
    """
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        resp = _requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("title", video_id)
    except Exception:
        pass
    return video_id