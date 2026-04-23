from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class SourceRecord(BaseModel):
    source_id: str
    title: str
    url: str
    category: str
    source_type: Literal["pdf", "html"]
    campus: str | None = None
    priority: str | None = None


class DocumentChunk(BaseModel):
    chunk_id: str
    source_id: str
    chunk_index: int
    text: str
    title: str
    url: str
    category: str
    source_type: Literal["pdf", "html"]
    campus: str | None = None


class Citation(BaseModel):
    title: str
    url: str
    category: str
    excerpt: str
    score: float
    source_type: Literal["pdf", "html"]
    campus: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    mode: Literal["ollama", "cloud", "compare"] | None = None
    top_k: int = Field(default=5, ge=1, le=10)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ProviderAnswer(BaseModel):
    provider: Literal["ollama", "cloud"]
    answer: str
    latency_ms: int
    error: str | None = None


class ChatResponse(BaseModel):
    mode: Literal["ollama", "cloud", "compare"]
    answer: str
    citations: list[Citation]
    providers: list[ProviderAnswer] = Field(default_factory=list)
    min_score: float


class IngestRequest(BaseModel):
    source: str | None = None
    reset: bool = True
    limit: int | None = Field(default=None, ge=1)


class IngestSummary(BaseModel):
    source_file: str
    sources_found: int
    sources_processed: int
    chunks_indexed: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


class EvaluateRequest(BaseModel):
    mode: Literal["ollama", "cloud", "compare"] = "compare"
    output: str = "data/exports/evaluation_results.csv"
    max_questions: int | None = Field(default=None, ge=1)
    include_baseline: bool = True


class EvaluationSummary(BaseModel):
    output: str
    questions: int
    mode: Literal["ollama", "cloud", "compare"]
    include_baseline: bool


class HealthResponse(BaseModel):
    app: str
    qdrant: str
    ollama: str
    collection: str

