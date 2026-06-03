"""
transcript_service.py — Fetches the transcript of a YouTube video.

Uses youtube-transcript-api which works without any API key.
Tries the requested language first, then falls back to auto-generated captions,
then to any available language.
"""

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from backend.utils.youtube_utils import extract_video_id


class TranscriptResult:
    """Holds the raw transcript text plus metadata."""

    def __init__(self, video_id: str, text: str, language: str, title: str = ""):
        self.video_id = video_id
        self.text = text
        self.language = language
        self.title = title


def fetch_transcript(url: str, preferred_language: str = "en") -> TranscriptResult:
    """
    Given a YouTube URL, return a TranscriptResult.

    Steps:
      1. Extract video ID from URL.
      2. Try to get transcript in preferred_language.
      3. Fall back to any available transcript (auto-generated included).
      4. Raise descriptive errors on failure.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract a valid video ID from URL: {url}")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except VideoUnavailable:
        raise ValueError(f"Video '{video_id}' is unavailable or private.")
    except TranscriptsDisabled:
        raise ValueError(f"Transcripts are disabled for video '{video_id}'.")
    except Exception as e:
        raise ValueError(f"Could not retrieve transcripts: {e}")

    # Try preferred language first, then any language
    transcript = None
    used_language = preferred_language

    try:
        transcript = transcript_list.find_transcript([preferred_language])
        used_language = preferred_language
    except NoTranscriptFound:
        pass

    if transcript is None:
        # Try auto-generated in preferred language
        try:
            transcript = transcript_list.find_generated_transcript([preferred_language])
            used_language = preferred_language + " (auto)"
        except NoTranscriptFound:
            pass

    if transcript is None:
        # Fall back to whatever is available
        available = list(transcript_list)
        if not available:
            raise ValueError(f"No transcripts available for video '{video_id}'.")
        transcript = available[0]
        used_language = transcript.language_code

    # Fetch and join transcript segments into one string
    segments = transcript.fetch()
    full_text = " ".join(seg["text"].strip() for seg in segments)
    full_text = full_text.replace("\n", " ").strip()

    # Try to get video title via a lightweight approach
    title = _get_video_title(video_id)

    return TranscriptResult(
        video_id=video_id,
        text=full_text,
        language=used_language,
        title=title,
    )


def _get_video_title(video_id: str) -> str:
    """
    Attempt to get the video title without needing a YouTube API key.
    Uses the oEmbed endpoint which is publicly available.
    Falls back to the video ID if it fails.
    """
    try:
        import requests
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=5)
        if response.status_code == 200:
            return response.json().get("title", video_id)
    except Exception:
        pass
    return video_id