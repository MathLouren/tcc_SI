from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.evaluate import run_evaluation
from app.ingest import ingest_sources
from app.rag import RagService
from app.schemas import (
    ChatRequest,
    ChatResponse,
    EvaluateRequest,
    EvaluationSummary,
    HealthResponse,
    IngestRequest,
    IngestSummary,
)
from app.source_parser import parse_source_file

settings = get_settings()
rag_service = RagService(settings)

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    qdrant_status = await _check_url(f"{settings.qdrant_url.rstrip('/')}/collections")
    ollama_status = await _check_url(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
    return HealthResponse(
        app="ok",
        qdrant=qdrant_status,
        ollama=ollama_status,
        collection=settings.qdrant_collection,
    )


@app.get("/api/sources")
async def sources() -> dict:
    parsed = parse_source_file(settings.source_file)
    categories: dict[str, int] = {}
    types: dict[str, int] = {"pdf": 0, "html": 0}
    for source in parsed:
        categories[source.category] = categories.get(source.category, 0) + 1
        types[source.source_type] = types.get(source.source_type, 0) + 1

    return {
        "source_file": settings.source_file,
        "total": len(parsed),
        "types": types,
        "categories": categories,
        "sources": [source.model_dump() for source in parsed],
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await rag_service.answer(request)


@app.post("/api/ingest", response_model=IngestSummary)
async def ingest(request: IngestRequest) -> IngestSummary:
    return await run_in_threadpool(
        ingest_sources,
        request.source or settings.source_file,
        request.reset,
        request.limit,
        settings,
    )


@app.post("/api/evaluate", response_model=EvaluationSummary)
async def evaluate(request: EvaluateRequest) -> EvaluationSummary:
    return await run_evaluation(
        mode=request.mode,
        output=request.output,
        max_questions=request.max_questions,
        include_baseline=request.include_baseline,
        settings=settings,
    )


async def _check_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            return "ok" if response.status_code < 500 else f"erro_http_{response.status_code}"
    except Exception:
        return "indisponivel"

