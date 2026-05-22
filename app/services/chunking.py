"""Text chunking service — semantic + hierarchical.

Three chunking strategies:
  chunk_policy(text)   → 600-token semantic chunks for real policy documents
  chunk_starter(text)  → 400-token chunks for generic starter templates
  chunk_text(text)     → configurable fallback

Hierarchical (parent-child) chunking:
  hierarchical_chunks(text) → list[HChunk]

  Each document is first split into large semantic parent chunks (~800 tokens).
  Each parent is then split into small child chunks (~150 tokens) for embedding.
  Retrieval finds children (precise match), but the LLM receives the parent
  (rich context). If a parent is already ≤150 tokens it becomes a leaf directly.

Semantic splitting:
  Detects structural boundaries in security policy documents — markdown headers,
  numbered sections, ALL CAPS headings, and paragraph breaks — so chunks never
  cut a policy clause mid-thought.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Token approximation
# ---------------------------------------------------------------------------

def _approx_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.33))


# ---------------------------------------------------------------------------
# Semantic structural splitter
# ---------------------------------------------------------------------------

def _is_section_header(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if re.match(r'^#{1,6}\s+\S', s):           # ## Markdown header
        return True
    if re.match(r'^\d+[\.\d]*\s+[A-Z]', s):    # 1. / 2.1 / 3.1.2 Numbered section
        return True
    if s.isupper() and len(s) >= 5:             # ALL CAPS HEADING
        return True
    if re.match(r'^[A-Z][^.!?\n]{0,60}:\s*$', s):  # "Section Title:" label
        return True
    return False


def semantic_chunk(text: str, max_tokens: int = 800) -> list[str]:
    """Split text at structural boundaries, then cap each section at max_tokens."""
    lines = text.split('\n')
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if _is_section_header(line) and current:
            section = '\n'.join(current).strip()
            if section:
                sections.append(section)
            current = [line]
        else:
            current.append(line)

    if current:
        section = '\n'.join(current).strip()
        if section:
            sections.append(section)

    # If no structural breaks found, fall back to paragraph splitting
    if len(sections) <= 1:
        sections = [s.strip() for s in re.split(r'\n{2,}', text) if s.strip()]

    # Cap oversized sections at max_tokens by sentence-splitting
    result: list[str] = []
    for section in sections:
        if _approx_tokens(section) <= max_tokens:
            result.append(section)
        else:
            result.extend(chunk_text(section, chunk_size=max_tokens, overlap=80))

    return [r for r in result if r.strip()]


# ---------------------------------------------------------------------------
# Sentence-boundary chunk splitter (base)
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> list[str]:
    """Split text into overlapping chunks respecting sentence boundaries."""
    raw = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in raw if s.strip()]
    if not sentences:
        return []

    token_counts = [_approx_tokens(s) for s in sentences]
    chunks: list[str] = []
    start = 0

    while start < len(sentences):
        end, total = start, 0
        while end < len(sentences):
            if total > 0 and total + token_counts[end] > chunk_size:
                break
            total += token_counts[end]
            end += 1

        chunks.append(" ".join(sentences[start:end]))

        if end >= len(sentences):
            break

        overlap_total, next_start = 0, end
        for i in range(end - 1, start - 1, -1):
            if overlap_total + token_counts[i] > overlap:
                break
            overlap_total += token_counts[i]
            next_start = i

        start = max(start + 1, next_start)

    return chunks


def chunk_policy(text: str) -> list[str]:
    """Semantic chunks for real policy/compliance documents."""
    return semantic_chunk(text, max_tokens=600)


def chunk_starter(text: str) -> list[str]:
    """Smaller chunks for generic starter templates."""
    return chunk_text(text, chunk_size=400, overlap=50)


# ---------------------------------------------------------------------------
# Hierarchical (parent-child) chunking
# ---------------------------------------------------------------------------

_PARENT_MAX_TOKENS = 800
_CHILD_MAX_TOKENS  = 150
_CHILD_OVERLAP     = 20


@dataclass
class HChunk:
    text: str
    is_leaf: bool
    parent_index: int | None   # index in the returned list; None for top-level chunks


def hierarchical_chunks(text: str) -> list[HChunk]:
    """Return a flat list of HChunk objects describing a parent-child hierarchy.

    Parents are large semantic sections (≤800 tokens, is_leaf=False).
    Children are small sub-chunks of each parent (≤150 tokens, is_leaf=True).
    Only children are embedded for retrieval; parents provide LLM context.

    If a parent section is already small (≤150 tokens) it becomes a leaf
    directly with no children — avoiding unnecessary overhead on short sections.
    """
    parent_texts = semantic_chunk(text, max_tokens=_PARENT_MAX_TOKENS)
    result: list[HChunk] = []

    for parent_text in parent_texts:
        if _approx_tokens(parent_text) <= _CHILD_MAX_TOKENS:
            # Small enough to be a leaf on its own
            result.append(HChunk(text=parent_text, is_leaf=True, parent_index=None))
            continue

        parent_index = len(result)
        result.append(HChunk(text=parent_text, is_leaf=False, parent_index=None))

        children = chunk_text(parent_text, chunk_size=_CHILD_MAX_TOKENS, overlap=_CHILD_OVERLAP)
        for child_text in children:
            result.append(HChunk(text=child_text, is_leaf=True, parent_index=parent_index))

    return result
