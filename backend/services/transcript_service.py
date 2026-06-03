"""
transcript_service.py

Compatible with ALL versions of youtube-transcript-api:
  - v0.6.x  : YouTubeTranscriptApi.get_transcript(), list_transcripts() → dict segments
  - v1.0+   : YouTubeTranscriptApi.fetch() → FetchedTranscript object, no list_transcripts
"""

import requests as _requests
from backend.utils.youtube_utils import extract_video_id


class TranscriptResult:
    def __init__(self, video_id: str, text: str, language: str, title: str = ""):
        self.video_id = video_id
        self.text = text
        self.language = language
        self.title = title


def _segments_to_text(segments) -> str:
    """Convert segment list OR FetchedTranscript object to plain text string."""
    parts = []
    for seg in segments:
        if isinstance(seg, dict):
            parts.append(seg.get("text", "").strip())
        else:
            # v1.x FetchedTranscriptSnippet object
            text = getattr(seg, "text", None) or getattr(seg, "content", None) or str(seg)
            parts.append(text.strip())
    return " ".join(p for p in parts if p).replace("\n", " ").strip()


def _detect_api_version():
    """Return 'v1' or 'v0' based on what's installed."""
    import youtube_transcript_api as _yta
    ver = getattr(_yta, "__version__", "0")
    major = int(str(ver).split(".")[0]) if ver else 0
    return "v1" if major >= 1 else "v0"


def fetch_transcript(url: str, preferred_language: str = "en") -> TranscriptResult:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract a valid video ID from URL: {url}")

    try:
        import youtube_transcript_api as _yta
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError("youtube-transcript-api not installed. Run: pip install youtube-transcript-api")

    api_version = _detect_api_version()
    last_error = None

    # ─────────────────────────────────────────────
    #  v1.x  API  (fetch / FetchedTranscript)
    # ─────────────────────────────────────────────
    if api_version == "v1":
        # v1 uses: YouTubeTranscriptApi.fetch(video_id, languages=[...])
        for lang_args in (
            {"languages": [preferred_language]},
            {"languages": ["en"]},
            {},                                  # no preference → auto pick
        ):
            try:
                fetched = YouTubeTranscriptApi.fetch(video_id, **lang_args)
                text = _segments_to_text(fetched)
                if text:
                    used_lang = lang_args.get("languages", ["auto"])[0]
                    title = _get_video_title(video_id)
                    return TranscriptResult(video_id=video_id, text=text, language=used_lang, title=title)
            except Exception as e:
                last_error = e
                continue

        # v1 also exposes list_transcripts in some builds — try it
        if hasattr(YouTubeTranscriptApi, "list_transcripts"):
            try:
                tlist = YouTubeTranscriptApi.list_transcripts(video_id)
                for t in tlist:
                    try:
                        segments = t.fetch()
                        text = _segments_to_text(segments)
                        if text:
                            title = _get_video_title(video_id)
                            return TranscriptResult(
                                video_id=video_id, text=text,
                                language=t.language_code, title=title
                            )
                    except Exception:
                        continue
            except Exception as e:
                last_error = e

    # ─────────────────────────────────────────────
    #  v0.x  API  (get_transcript / list_transcripts)
    # ─────────────────────────────────────────────
    else:
        # Strategy A: direct get_transcript
        for lang_args in (
            {"languages": [preferred_language]},
            {"languages": ["en"]},
            {},
        ):
            try:
                segments = YouTubeTranscriptApi.get_transcript(video_id, **lang_args)
                text = _segments_to_text(segments)
                if text:
                    used_lang = lang_args.get("languages", ["auto"])[0]
                    title = _get_video_title(video_id)
                    return TranscriptResult(video_id=video_id, text=text, language=used_lang, title=title)
            except Exception as e:
                last_error = e
                continue

        # Strategy B: list_transcripts fallback
        try:
            tlist = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in list(tlist):
                try:
                    segments = t.fetch()
                    text = _segments_to_text(segments)
                    if text:
                        title = _get_video_title(video_id)
                        return TranscriptResult(
                            video_id=video_id, text=text,
                            language=t.language_code, title=title
                        )
                except Exception:
                    continue
        except Exception as e:
            last_error = e

    raise ValueError(
        f"Could not fetch transcript for '{video_id}'. "
        f"API version detected: {api_version}. "
        f"Last error: {last_error}"
    )


def _get_video_title(video_id: str) -> str:
    try:
        url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )
        resp = _requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("title", video_id)
    except Exception:
        pass
    return video_id