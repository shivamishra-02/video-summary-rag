"""
chunking_service.py — Splits a long transcript into overlapping text chunks.

Uses LangChain's RecursiveCharacterTextSplitter so chunks break on natural
sentence/word boundaries rather than mid-word.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def split_transcript(text: str) -> list[str]:
    """
    Split raw transcript text into overlapping chunks.

    Args:
        text: The full transcript as a single string.

    Returns:
        List of chunk strings. Minimum 1 chunk even for short transcripts.
    """
    if not text or not text.strip():
        raise ValueError("Transcript text is empty — nothing to chunk.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=[". ", "? ", "! ", "\n", " ", ""],  # prefer sentence boundaries
    )

    chunks = splitter.split_text(text)

    # Filter out whitespace-only chunks
    chunks = [c.strip() for c in chunks if c.strip()]

    if not chunks:
        # Edge case: text shorter than chunk_size
        chunks = [text.strip()]

    return chunks