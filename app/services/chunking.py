"""Text chunking service.

Splits text into overlapping chunks that respect sentence boundaries.
Token counts are approximated as word_count * 1.33 — no external tokenizer needed.
"""

import re


def _approx_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.33))


def _split_sentences(text: str) -> list[str]:
    """Split on whitespace that follows sentence-ending punctuation."""
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in raw if s.strip()]


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split *text* into overlapping chunks, respecting sentence boundaries.

    chunk_size and overlap are measured in approximate tokens (word_count * 1.33).
    Adjacent chunks share ~overlap tokens at their boundary.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    token_counts = [_approx_tokens(s) for s in sentences]
    chunks: list[str] = []
    start = 0

    while start < len(sentences):
        # Accumulate sentences until we would exceed chunk_size.
        end = start
        total = 0
        while end < len(sentences):
            if total > 0 and total + token_counts[end] > chunk_size:
                break
            total += token_counts[end]
            end += 1

        chunks.append(" ".join(sentences[start:end]))

        if end >= len(sentences):
            break

        # Back-track from `end` by ~overlap tokens to find the next start.
        overlap_total = 0
        next_start = end
        for i in range(end - 1, start - 1, -1):
            if overlap_total + token_counts[i] > overlap:
                break
            overlap_total += token_counts[i]
            next_start = i

        # Always advance at least one sentence to guarantee termination.
        start = max(start + 1, next_start)

    return chunks
