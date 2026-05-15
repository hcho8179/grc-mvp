"""Tests for the chunking service."""

import pytest

from app.services.chunking import chunk_text


class TestChunkText:
    def test_empty_string(self):
        assert chunk_text("") == []

    def test_whitespace_only(self):
        assert chunk_text("   \n\n   \t  ") == []

    def test_short_text_is_single_chunk(self):
        text = "This is a short sentence. It fits in one chunk."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert "short sentence" in chunks[0]

    def test_long_text_splits(self):
        # 30 words per sentence × 30 sentences ≈ 1197 tokens → splits at default chunk_size=500
        sentences = [f"Word{i} " * 30 + "ends here." for i in range(30)]
        text = " ".join(sentences)
        chunks = chunk_text(text)
        assert len(chunks) >= 2

    def test_all_text_is_covered(self):
        """No content should be silently dropped."""
        sentences = [f"Sentence number {i} is here." for i in range(60)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        combined = " ".join(chunks)
        for i in range(60):
            assert f"Sentence number {i}" in combined

    def test_overlap_shares_sentences(self):
        """Adjacent chunks should share content at their boundary."""
        sentences = [f"Unique sentence {i} ends." for i in range(60)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=150, overlap=40)
        assert len(chunks) >= 2
        # Words from the tail of chunk[0] should appear in the head of chunk[1]
        tail_words = set(chunks[0].split()[-15:])
        head_words = set(chunks[1].split()[:15])
        assert tail_words & head_words, "No overlap detected between chunk[0] and chunk[1]"

    def test_sentence_boundaries_respected(self):
        """Chunks must not split mid-sentence."""
        text = (
            "First sentence ends with a period. "
            "Second sentence also ends properly. "
            "Third one too. "
            "Fourth sentence here. "
        ) * 20
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        for chunk in chunks:
            stripped = chunk.strip()
            # Each chunk should end on a sentence boundary (period, !, ?)
            assert stripped[-1] in ".!?", (
                f"Chunk does not end on sentence boundary: ...{stripped[-30:]!r}"
            )

    def test_smaller_chunk_size_produces_more_chunks(self):
        sentences = [f"This is test sentence number {i}." for i in range(40)]
        text = " ".join(sentences)
        small = chunk_text(text, chunk_size=80, overlap=15)
        large = chunk_text(text, chunk_size=300, overlap=15)
        assert len(small) > len(large)

    def test_single_long_sentence_becomes_one_chunk(self):
        # A single sentence much longer than chunk_size should not cause infinite loop
        long_sentence = "word " * 500 + "."
        chunks = chunk_text(long_sentence, chunk_size=100, overlap=20)
        assert len(chunks) == 1

    def test_overlap_does_not_exceed_chunk_size(self):
        sentences = [f"Sentence {i}." for i in range(40)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=100, overlap=30)
        from app.services.chunking import _approx_tokens
        for chunk in chunks:
            # Each chunk should be at most roughly chunk_size + one sentence's worth of tokens
            assert _approx_tokens(chunk) <= 200  # generous upper bound
