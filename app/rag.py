from __future__ import annotations

from app.config import Settings
from app.embeddings import EmbeddingService
from app.llm import LLMService
from app.schemas import ChatRequest, ChatResponse, Citation, ProviderAnswer
from app.vector_store import VectorStore

REFUSAL = "não encontrei nas fontes oficiais disponíveis para responder com segurança."


class RagService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embeddings = EmbeddingService(settings)
        self.store = VectorStore(settings)
        self.llm = LLMService(settings)

    def retrieve(self, question: str, top_k: int) -> list[Citation]:
        query_vector = self.embeddings.encode([question])[0]
        results = self.store.search(query_vector, limit=top_k)
        citations: list[Citation] = []
        for result in results:
            payload = result.payload or {}
            excerpt = str(payload.get("text", "")).strip()
            if len(excerpt) > 700:
                excerpt = excerpt[:697].rsplit(" ", 1)[0] + "..."
            citations.append(
                Citation(
                    title=str(payload.get("title", "Fonte sem titulo")),
                    url=str(payload.get("url", "")),
                    category=str(payload.get("category", "Sem categoria")),
                    excerpt=excerpt,
                    score=float(result.score),
                    source_type=payload.get("source_type", "html"),
                    campus=payload.get("campus"),
                )
            )
        return citations

    async def answer(self, request: ChatRequest) -> ChatResponse:
        mode = request.mode or self.settings.llm_mode
        if mode not in {"ollama", "cloud", "compare"}:
            mode = "ollama"

        min_score = request.min_score or self.settings.min_retrieval_score
        citations = self.retrieve(request.question, request.top_k)
        if not citations or citations[0].score < min_score:
            providers = _refusal_providers(mode)
            return ChatResponse(
                mode=mode,
                answer=REFUSAL,
                citations=[],
                providers=providers,
                min_score=min_score,
            )

        prompt = build_prompt(request.question, citations)
        if mode == "compare":
            providers = [
                await self.llm.generate("ollama", prompt),
                await self.llm.generate("cloud", prompt),
            ]
            answer = "Comparacao concluida. Veja as respostas por provedor."
        else:
            provider = await self.llm.generate(mode, prompt)
            providers = [provider]
            answer = provider.answer

        return ChatResponse(
            mode=mode,
            answer=answer,
            citations=citations,
            providers=providers,
            min_score=min_score,
        )


def build_prompt(question: str, citations: list[Citation]) -> str:
    context_lines = []
    for index, citation in enumerate(citations, start=1):
        campus = f" | campus: {citation.campus}" if citation.campus else ""
        context_lines.append(
            f"[{index}] {citation.title} | {citation.category}{campus} | {citation.url}\n"
            f"{citation.excerpt}"
        )

    context = "\n\n".join(context_lines)
    return f"""Voce e um assistente de atendimento academico da UNIVERSO.
Use somente as fontes oficiais abaixo para responder.
Sempre cite as fontes usando marcadores como [1], [2].
Se as fontes nao forem suficientes, responda exatamente: "{REFUSAL}"
Nao invente prazos, regras, valores, documentos ou links.

FONTES RECUPERADAS:
{context}

PERGUNTA DO USUARIO:
{question}

RESPOSTA:"""


def build_no_rag_prompt(question: str) -> str:
    return f"""Responda em portugues do Brasil, sem consultar fontes externas.

PERGUNTA:
{question}

RESPOSTA:"""


def _refusal_providers(mode: str) -> list[ProviderAnswer]:
    if mode == "compare":
        providers = ["ollama", "cloud"]
    else:
        providers = [mode]
    return [
        ProviderAnswer(provider=provider, answer=REFUSAL, latency_ms=0)
        for provider in providers
        if provider in {"ollama", "cloud"}
    ]

