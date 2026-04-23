from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "UNIVERSO RAG Chatbot"
    source_file: str = "universo_links_tcc_2.md"
    data_dir: Path = Path("data")
    cache_dir: Path = Path("data/cache")
    exports_dir: Path = Path("data/exports")

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = Field(default="universo_rag_sources", alias="QDRANT_COLLECTION")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    llm_mode: str = "ollama"

    cloud_api_base_url: str = "https://api.openai.com/v1"
    cloud_api_key: str = ""
    cloud_model: str = ""

    min_retrieval_score: float = 0.35
    chunk_size: int = 1400
    chunk_overlap: int = 180
    request_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings

