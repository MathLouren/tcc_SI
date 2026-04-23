from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.chunking import make_chunks
from app.config import Settings, get_settings
from app.downloader import download_source
from app.embeddings import EmbeddingService
from app.extractors import extract_text
from app.schemas import IngestSummary
from app.source_parser import parse_source_file
from app.vector_store import VectorStore

LOGGER = logging.getLogger(__name__)


def ingest_sources(
    source_path: str | Path | None = None,
    reset: bool = False,
    limit: int | None = None,
    settings: Settings | None = None,
) -> IngestSummary:
    settings = settings or get_settings()
    source_file = Path(source_path or settings.source_file)
    sources = parse_source_file(source_file)
    if limit:
        sources = sources[:limit]

    embeddings = EmbeddingService(settings)
    vector_size = embeddings.dimension
    store = VectorStore(settings)
    if reset:
        store.reset_collection(vector_size)
    else:
        store.ensure_collection(vector_size)

    processed = 0
    indexed = 0
    skipped = 0
    errors: list[str] = []

    for source in sources:
        try:
            cache_path = download_source(source, settings)
            text = extract_text(cache_path, source)
            chunks = make_chunks(
                source,
                text,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )
            if not chunks:
                skipped += 1
                errors.append(f"Sem texto extraido: {source.title} ({source.url})")
                continue

            vectors = embeddings.encode([chunk.text for chunk in chunks])
            store.upsert_chunks(chunks, vectors)
            processed += 1
            indexed += len(chunks)
            LOGGER.info("Indexado: %s (%s chunks)", source.title, len(chunks))
        except Exception as exc:
            skipped += 1
            message = f"{source.title} ({source.url}): {exc}"
            LOGGER.warning(message)
            errors.append(message)

    return IngestSummary(
        source_file=str(source_file),
        sources_found=len(sources),
        sources_processed=processed,
        chunks_indexed=indexed,
        skipped=skipped,
        errors=errors,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingere fontes publicas da UNIVERSO no Qdrant.")
    parser.add_argument("--source", default="universo_links_tcc_2.md")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    summary = ingest_sources(source_path=args.source, reset=args.reset, limit=args.limit)
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

