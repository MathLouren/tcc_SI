from __future__ import annotations

from qdrant_client import QdrantClient, models

from app.config import Settings
from app.schemas import DocumentChunk


class VectorStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection

    def ensure_collection(self, vector_size: int) -> None:
        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def reset_collection(self, vector_size: int) -> None:
        if self.client.collection_exists(self.collection_name):
            self.client.delete_collection(self.collection_name)
        self.ensure_collection(vector_size)

    def upsert_chunks(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors must have the same length.")
        if not chunks:
            return

        points = [
            models.PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload=chunk.model_dump(),
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector: list[float], limit: int) -> list[models.ScoredPoint]:
        if not self.client.collection_exists(self.collection_name):
            return []
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )

    def count(self) -> int:
        if not self.client.collection_exists(self.collection_name):
            return 0
        result = self.client.count(collection_name=self.collection_name, exact=True)
        return int(result.count)
