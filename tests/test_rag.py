"""
test_rag.py — Unit tests for chunking, embedding, and vector store.
Run with:  pytest tests/test_rag.py -v
No external API calls needed for these tests.
"""

import numpy as np
import pytest
from backend.services.chunking_service import split_transcript
from backend.services.embedding_service import embed_texts, embed_query, get_embedding_dimension
from backend.services import vector_store


class TestChunking:
    def test_basic_split(self):
        text = "Hello world. " * 200   # long enough to split
        chunks = split_transcript(text)
        assert len(chunks) > 1

    def test_short_text_returns_one_chunk(self):
        text = "This is a short transcript."
        chunks = split_transcript(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text_raises(self):
        with pytest.raises(ValueError):
            split_transcript("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            split_transcript("   \n  ")

    def test_chunks_cover_full_content(self):
        """Every word in the original text should appear in at least one chunk."""
        text = "The quick brown fox jumps over the lazy dog. " * 50
        chunks = split_transcript(text)
        combined = " ".join(chunks)
        assert "quick brown fox" in combined


class TestEmbedding:
    def test_embed_texts_shape(self):
        texts = ["Hello world", "How are you"]
        embeddings = embed_texts(texts)
        assert embeddings.shape[0] == 2
        assert embeddings.dtype == np.float32

    def test_embed_query_shape(self):
        emb = embed_query("What is this video about?")
        assert emb.shape[0] == 1

    def test_embedding_dimension_positive(self):
        dim = get_embedding_dimension()
        assert dim > 0

    def test_empty_list_raises(self):
        with pytest.raises(ValueError):
            embed_texts([])

    def test_empty_query_raises(self):
        with pytest.raises(ValueError):
            embed_query("")


class TestVectorStore:
    def _make_dummy_index(self, video_id: str = "test123"):
        chunks = ["chunk one about cats", "chunk two about dogs", "chunk three about birds"]
        embeddings = embed_texts(chunks)
        vector_store.add_video(
            video_id=video_id,
            title="Test Video",
            language="en",
            chunks=chunks,
            embeddings=embeddings,
        )
        return chunks

    def test_add_and_search(self):
        chunks = self._make_dummy_index("vtest_search")
        q_emb = embed_query("tell me about cats")
        results = vector_store.search("vtest_search", q_emb, top_k=2)
        assert len(results) == 2
        assert "text" in results[0]
        assert "distance" in results[0]

    def test_video_exists(self):
        self._make_dummy_index("vtest_exists")
        assert vector_store.video_exists("vtest_exists") is True
        assert vector_store.video_exists("nonexistent") is False

    def test_delete_video(self):
        self._make_dummy_index("vtest_delete")
        assert vector_store.delete_video("vtest_delete") is True
        assert vector_store.video_exists("vtest_delete") is False

    def test_search_missing_video_raises(self):
        q_emb = embed_query("something")
        with pytest.raises(KeyError):
            vector_store.search("video_that_doesnt_exist", q_emb)

    def test_list_videos(self):
        self._make_dummy_index("vtest_list")
        videos = vector_store.list_videos()
        ids = [v.video_id for v in videos]
        assert "vtest_list" in ids