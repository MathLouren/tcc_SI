from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.schemas import SourceRecord


class DownloadError(RuntimeError):
    pass


def cache_path_for(source: SourceRecord, settings: Settings) -> Path:
    parsed = urlparse(source.url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".pdf", ".html", ".htm"}:
        suffix = ".pdf" if source.source_type == "pdf" else ".html"
    digest = hashlib.sha1(source.url.encode("utf-8")).hexdigest()[:16]
    return settings.cache_dir / f"{digest}{suffix}"


def download_source(source: SourceRecord, settings: Settings, force: bool = False) -> Path:
    settings.ensure_dirs()
    path = cache_path_for(source, settings)
    if path.exists() and path.stat().st_size > 0 and not force:
        return path

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; UniversoRAGTCC/1.0; "
            "+https://universo.edu.br)"
        )
    }
    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=settings.request_timeout_seconds,
            headers=headers,
        ) as client:
            response = client.get(source.url)
            response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network dependent
        raise DownloadError(f"Falha ao baixar {source.url}: {exc}") from exc

    path.write_bytes(response.content)
    return path

