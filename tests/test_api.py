from fastapi.testclient import TestClient

from app import main
from app.schemas import ChatResponse, Citation, ProviderAnswer


def test_health_shape() -> None:
    client = TestClient(main.app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "ok"
    assert "qdrant" in payload
    assert "ollama" in payload


def test_chat_endpoint_returns_citations(monkeypatch) -> None:
    async def fake_answer(request):
        return ChatResponse(
            mode=request.mode or "ollama",
            answer="Resposta com fonte [1].",
            citations=[
                Citation(
                    title="MIA",
                    url="https://universo.edu.br/mia/",
                    category="Manuais",
                    excerpt="Trecho recuperado.",
                    score=0.91,
                    source_type="html",
                )
            ],
            providers=[
                ProviderAnswer(
                    provider="ollama",
                    answer="Resposta com fonte [1].",
                    latency_ms=1,
                )
            ],
            min_score=0.35,
        )

    monkeypatch.setattr(main.rag_service, "answer", fake_answer)
    client = TestClient(main.app)
    response = client.post("/api/chat", json={"question": "Onde vejo o MIA?", "mode": "ollama"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"][0]["title"] == "MIA"

