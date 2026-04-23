from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

from app.schemas import SourceRecord

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
PLAIN_URL_RE = re.compile(r"(https?://[^\s|)]+)")


def parse_source_file(path: Path | str) -> list[SourceRecord]:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8-sig")

    sources: list[SourceRecord] = []
    current_category = "Sem categoria"
    current_priority: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_category = _clean_heading(line)
            current_priority = _extract_priority(line)
            continue

        if current_category.lower().startswith("links externos relacionados"):
            continue

        if not line.startswith("|") or "---" in line:
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower().startswith("descri"):
            continue

        url = _extract_url(cells[1])
        if not url:
            continue

        title = _strip_markdown(cells[0])
        if not title:
            title = _extract_markdown_title(cells[1]) or url

        source_type = "pdf" if ".pdf" in url.lower().split("?")[0] else "html"
        source_id = hashlib.sha1(url.encode("utf-8")).hexdigest()
        sources.append(
            SourceRecord(
                source_id=source_id,
                title=title,
                url=url,
                category=current_category,
                source_type=source_type,
                campus=_infer_campus(f"{title} {url} {current_category}"),
                priority=current_priority,
            )
        )

    return sources


def _extract_url(cell: str) -> str | None:
    markdown = MARKDOWN_LINK_RE.search(cell)
    if markdown:
        return markdown.group(2)
    plain = PLAIN_URL_RE.search(cell)
    if plain:
        return plain.group(1)
    return None


def _extract_markdown_title(cell: str) -> str | None:
    markdown = MARKDOWN_LINK_RE.search(cell)
    if markdown:
        return _strip_markdown(markdown.group(1))
    return None


def _strip_markdown(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = value.replace("&mdash;", "-").strip()
    return re.sub(r"\s+", " ", value)


def _clean_heading(line: str) -> str:
    heading = line.lstrip("#").strip()
    heading = heading.replace("â€”", "-").replace("—", "-")
    heading = re.sub(r"\[(PDFs|HTML)\]\s*$", "", heading, flags=re.IGNORECASE).strip()
    heading = re.sub(r"^[^\wÀ-ÿ]+", "", heading).strip()

    if "PRIORIDADE" in heading.upper() and "-" in heading:
        heading = heading.split("-", 1)[1].strip()

    return re.sub(r"\s+", " ", heading)


def _extract_priority(line: str) -> str | None:
    clean = _clean_heading(line)
    upper = line.upper()
    if "PRIORIDADE M" in upper:
        return "maxima"
    if "PRIORIDADE ALTA" in upper:
        return "alta"
    if "PRIORIDADE" in upper:
        return "prioridade"
    if "Manuais do Aluno" in clean:
        return "maxima"
    return None


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return value.casefold()


def _infer_campus(value: str) -> str | None:
    text = _normalize(value)
    campuses = [
        ("sao-goncalo", ["sao goncalo", "sao-goncalo"]),
        ("niteroi", ["niteroi"]),
        ("itaipu", ["itaipu"]),
        ("campos", ["campos", "campos dos goytacazes"]),
        ("belo-horizonte", ["belo horizonte", "bh-l", "universo-bh"]),
        ("goiania", ["goiania", "go-l", "universo-go"]),
        ("juiz-de-fora", ["juiz de fora", "jf-l", "universo-jf"]),
        ("recife", ["recife", "re-l", "universo-re"]),
        ("salvador", ["salvador", "sa-l", "universo-sa"]),
        ("ead", ["ead"]),
    ]
    matches = [campus for campus, keys in campuses if any(key in text for key in keys)]
    if not matches:
        return None
    return ", ".join(dict.fromkeys(matches))
