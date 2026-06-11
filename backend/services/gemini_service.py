"""
gemini_service.py — Wraps Google Gemini API (gemini-2.0-flash).
API key is validated at request time, not at import/startup.
"""

import google.generativeai as genai
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

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
    if not context_chunks:
        return "I'm sorry, I couldn't find information about that in this video."

    # Validate key at request time — not at startup
    api_key = GEMINI_API_KEY
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it in Railway → Variables."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)

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
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e