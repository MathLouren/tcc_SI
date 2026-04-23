from pathlib import Path

from app.extractors import extract_text
from app.schemas import SourceRecord


def test_extract_html_text_returns_visible_content(tmp_path: Path) -> None:
    html_path = tmp_path / "sample.html"
    html_path.write_text(
        "<html><head><title>Biblioteca</title><style>.x{}</style></head>"
        "<body><nav>menu</nav><main>Acervo digital da UNIVERSO</main></body></html>",
        encoding="utf-8",
    )
    source = SourceRecord(
        source_id="html",
        title="Biblioteca",
        url="https://universo.edu.br/biblioteca/",
        category="Campus Digital",
        source_type="html",
    )

    text = extract_text(html_path, source)

    assert "Biblioteca" in text
    assert "Acervo digital da UNIVERSO" in text
    assert "menu" not in text

