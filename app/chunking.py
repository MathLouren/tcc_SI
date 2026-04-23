from __future__ import annotations

import uuid

from app.schemas import DocumentChunk, SourceRecord


def make_chunks(
    source: SourceRecord,
    text: str,
    chunk_size: int = 1400,
    overlap: int = 180,
) -> list[DocumentChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            sentence_break = normalized.rfind(". ", start, end)
            if sentence_break > start + chunk_size // 2:
                end = sentence_break + 1

        chunk_text = normalized[start:end].strip()
        if len(chunk_text) >= 80 or not chunks:
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source.url}#{len(chunks)}"))
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    source_id=source.source_id,
                    chunk_index=len(chunks),
                    text=chunk_text,
                    title=source.title,
                    url=source.url,
                    category=source.category,
                    source_type=source.source_type,
                    campus=source.campus,
                )
            )

        if end >= length:
            break
        next_start = max(end - overlap, start + 1)
        start = next_start

    return chunks

