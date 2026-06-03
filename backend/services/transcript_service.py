"""
transcript_service.py

youtube-transcript-api v1.2.4
fetch() and list() are INSTANCE methods, not class methods.
Usage: YouTubeTranscriptApi().fetch(video_id, languages=[...])
"""

import requests as _requests
from backend.utils.youtube_utils import extract_video_id


class TranscriptResult:
    def __init__(self, video_id: str, text: str, language: str, title: str = ""):
        self.video_id = video_id
        self.text = text
        self.language = language
        self.title = title


def _to_text(fetched) -> str:
    parts = []
    for snippet in fetched:
        if isinstance(snippet, dict):
            t = snippet.get("text", "")
        else:
            t = getattr(snippet, "text", "") or str(snippet)
        t = t.strip()
        if t:
            parts.append(t)
    return " ".join(parts).replace("\n", " ").strip()


def fetch_transcript(url: str, preferred_language: str = "en") -> TranscriptResult:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract a valid video ID from URL: {url}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("Run: pip install youtube-transcript-api")

    # v1.2.4: instance methods — create ONE instance and reuse
    api = YouTubeTranscriptApi()
    last_error = None

    # ── Strategy 1: fetch() with language preferences ─────────────────────────
    for lang_list in [
        [preferred_language],
        ["en"],
        ["hi"],
        ["en-US"],
        ["en-GB"],
    ]:
        try:
            fetched = api.fetch(video_id, languages=lang_list)
            text = _to_text(fetched)
            if text:
                return TranscriptResult(
                    video_id=video_id, text=text,
                    language=lang_list[0],
                    title=_get_video_title(video_id),
                )
        except Exception as e:
            last_error = e

    # ── Strategy 2: fetch() with default language (library picks) ────────────
    try:
        fetched = api.fetch(video_id)
        text = _to_text(fetched)
        if text:
            return TranscriptResult(
                video_id=video_id, text=text,
                language="auto",
                title=_get_video_title(video_id),
            )
    except Exception as e:
        last_error = e

    # ── Strategy 3: list() → iterate every available transcript ──────────────
    try:
        transcript_list = api.list(video_id)
        for transcript in transcript_list:
            try:
                fetched = transcript.fetch()
                text = _to_text(fetched)
                if text:
                    lang = getattr(transcript, "language_code",
                           getattr(transcript, "language", "unknown"))
                    return TranscriptResult(
                        video_id=video_id, text=text,
                        language=lang,
                        title=_get_video_title(video_id),
                    )
            except Exception as e:
                last_error = e
                continue
    except Exception as e:
        last_error = e

    raise ValueError(
        f"Could not fetch transcript for '{video_id}'. "
        f"Last error: {last_error}"
    )


def _get_video_title(video_id: str) -> str:
    try:
        resp = _requests.get(
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json",
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("title", video_id)
    except Exception:
        pass
    return video_id