"""
config.py — All environment variables and app-level constants live here.
Every other module imports from here; never call os.getenv() elsewhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.0-flash"          # free-tier model

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 50))

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", 4))

# ── Similarity threshold ──────────────────────────────────────────────────────
# L2 distance — chunks with distance > this are considered "out of scope"
SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 1.2))

# ── Server ────────────────────────────────────────────────────────────────────
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", 8000))

# ── Validation ────────────────────────────────────────────────────────────────
if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set. "
        "Copy .env.example → .env and add your key from https://aistudio.google.com"
    )