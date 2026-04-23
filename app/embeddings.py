from __future__ import annotations

from functools import cached_property

from sentence_transformers import SentenceTransformer

from app.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.settings = settings

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self.settings.embedding_model)

    @property
    def dimension(self) -> int:
        dimension = self.model.get_sentence_embedding_dimension()
        if not dimension:
            vector = self.encode(["dimension check"])[0]
            return len(vector)
        return int(dimension)

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

