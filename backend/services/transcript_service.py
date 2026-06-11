"""
transcript_service.py

Supports BOTH versions automatically:
  v0.6.x (Python 3.14 / Streamlit Cloud): get_transcript(), list_transcripts()
  v1.x   (local dev):                     api.fetch(), api.list()  [instance methods]
"""

import requests as _requests
from backend.utils.youtube_utils import extract_video_id


class TranscriptResult:
    def __init__(self, video_id: str, text: str, language: str, title: str = ""):
        self.video_id = video_id
        self.text = text
        self.language = language
        self.title = title


def _to_text(segments) -> str:
    parts = []
    for s in segments:
        if isinstance(s, dict):
            t = s.get("text", "")
        else:
            t = getattr(s, "text", None) or getattr(s, "content", None) or str(s)
        t = t.strip()
        if t:
            parts.append(t)
    return " ".join(parts).replace("\n", " ").strip()


def _has_instance_methods() -> bool:
    """v1.x uses instance methods (self), v0.x uses class methods."""
    try:
        import inspect
        from youtube_transcript_api import YouTubeTranscriptApi
        fetch = getattr(YouTubeTranscriptApi, "fetch", None)
        if fetch is None:
            return False
        sig = str(inspect.signature(fetch))
        return sig.startswith("(self")
    except Exception:
        return False


def fetch_transcript(url: str, preferred_language: str = "en") -> TranscriptResult:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract a valid video ID from URL: {url}")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("Run: pip install youtube-transcript-api")

    last_error = None

    # ── v1.x path: instance methods ──────────────────────────────────────────
    if _has_instance_methods():
        api = YouTubeTranscriptApi()

        for kwargs in [{"languages": [preferred_language]}, {"languages": ["en"]},
                       {"languages": ["hi"]}, {}]:
            try:
                fetched = api.fetch(video_id, **kwargs)
                text = _to_text(fetched)
                if text:
                    lang = kwargs.get("languages", ["auto"])[0] if kwargs else "auto"
                    return TranscriptResult(video_id=video_id, text=text,
                                            language=lang, title=_get_video_title(video_id))
            except Exception as e:
                last_error = e

        try:
            for transcript in api.list(video_id):
                try:
                    text = _to_text(transcript.fetch())
                    if text:
                        lang = getattr(transcript, "language_code", "unknown")
                        return TranscriptResult(video_id=video_id, text=text,
                                                language=lang, title=_get_video_title(video_id))
                except Exception as e:
                    last_error = e
        except Exception as e:
            last_error = e

    # ── v0.x path: class methods ──────────────────────────────────────────────
    else:
        # Strategy 1: get_transcript() direct call
        for lang_args in [{"languages": [preferred_language]}, {"languages": ["en"]},
                          {"languages": ["hi"]}, {}]:
            try:
                segments = YouTubeTranscriptApi.get_transcript(video_id, **lang_args)
                text = _to_text(segments)
                if text:
                    lang = lang_args.get("languages", ["auto"])[0] if lang_args else "auto"
                    return TranscriptResult(video_id=video_id, text=text,
                                            language=lang, title=_get_video_title(video_id))
            except Exception as e:
                last_error = e

        # Strategy 2: list_transcripts() fallback
        try:
            tlist = YouTubeTranscriptApi.list_transcripts(video_id)
            for transcript in tlist:
                try:
                    text = _to_text(transcript.fetch())
                    if text:
                        lang = getattr(transcript, "language_code", "unknown")
                        return TranscriptResult(video_id=video_id, text=text,
                                                language=lang, title=_get_video_title(video_id))
                except Exception as e:
                    last_error = e
        except Exception as e:
            last_error = e

    raise ValueError(
        f"Could not fetch transcript for '{video_id}'. Last error: {last_error}"
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