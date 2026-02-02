
from __future__ import annotations
from typing import List

def simple_chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 120) -> List[str]:
    """Naive character-based splitter with overlap."""
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks
