from pathlib import Path

from app.source_parser import parse_source_file


def test_parse_universo_sources_counts() -> None:
    sources = parse_source_file(Path("universo_links_tcc_2.md"))

    assert len(sources) == 120
    assert sum(1 for source in sources if source.source_type == "pdf") == 17
    assert sum(1 for source in sources if source.source_type == "html") == 103
    assert any("MIA" in source.title for source in sources)
    assert any("Analise" in source.title or "Análise" in source.title for source in sources)


def test_source_metadata_has_category_and_id() -> None:
    sources = parse_source_file(Path("universo_links_tcc_2.md"))
    first = sources[0]

    assert first.source_id
    assert first.category
    assert first.url.startswith("https://")

