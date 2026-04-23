from app.chunking import make_chunks
from app.schemas import SourceRecord


def test_make_chunks_preserves_metadata() -> None:
    source = SourceRecord(
        source_id="abc",
        title="Manual do Aluno",
        url="https://universo.edu.br/manual.pdf",
        category="Manuais do Aluno",
        source_type="pdf",
        campus="niteroi",
    )
    text = "Regras academicas da UNIVERSO. " * 120

    chunks = make_chunks(source, text, chunk_size=300, overlap=50)

    assert len(chunks) > 1
    assert chunks[0].url == source.url
    assert chunks[0].category == source.category
    assert chunks[0].source_type == "pdf"

