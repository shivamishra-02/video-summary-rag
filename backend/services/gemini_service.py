"""
gemini_service.py — Wraps the Google Gemini API (gemini-1.5-flash).

Builds a grounded prompt from retrieved chunks and the user query,
then returns the model's answer as a plain string.
"""

import google.generativeai as genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

# Configure once at import time
genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(GEMINI_MODEL)

# ── System prompt ─────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions STRICTLY based on the \
provided video transcript excerpts.

Rules you MUST follow:
1. Answer ONLY from the context given below — do not use outside knowledge.
2. If the answer is not present in the context, respond with exactly:
   "I'm sorry, I couldn't find information about that in this video."
3. Be concise, factual, and cite relevant details from the context.
4. Do not make up information, speculate, or add content not in the context.
"""


def generate_answer(query: str, context_chunks: list[str]) -> str:
    """
    Ask Gemini to answer the query using only the provided context chunks.

    Args:
        query:          The user's question.
        context_chunks: List of relevant transcript chunks retrieved via FAISS.

    Returns:
        The model's answer as a string.
    """
    if not context_chunks:
        return "I'm sorry, I couldn't find information about that in this video."

    # Build numbered context block
    context_block = "\n\n".join(
        f"[Excerpt {i + 1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)
    )

    full_prompt = f"""{_SYSTEM_PROMPT}

─────────────── VIDEO TRANSCRIPT EXCERPTS ───────────────
{context_block}
─────────────────────────────────────────────────────────

Question: {query}

Answer:"""

    try:
        response = _model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e