from __future__ import annotations

import argparse
import asyncio
import csv
import json
from pathlib import Path

from app.config import Settings, get_settings
from app.llm import LLMService
from app.rag import RagService, build_no_rag_prompt
from app.schemas import ChatRequest, EvaluationSummary

QUESTION_SET = [
    ("Quais sao os direitos e deveres do aluno?", "Manuais do Aluno"),
    ("Onde encontro o calendario academico?", "Campus Digital"),
    ("Quais sao as formas de ingresso na UNIVERSO?", "Formas de Ingresso"),
    ("A UNIVERSO possui regras para concessao de bolsas?", "Bolsas"),
    ("Como acesso a biblioteca ou acervo digital?", "Campus Digital"),
    ("Quais unidades/campi da UNIVERSO aparecem nas fontes?", "Paginas das Unidades"),
    ("Quanto tempo dura o curso de Analise e Desenvolvimento de Sistemas?", "Cursos de Graduacao"),
    ("Onde o aluno acessa disciplinas online EAD?", "Campus Digital"),
    ("O que e a CPA da UNIVERSO?", "Institucional"),
    ("Quais informacoes aparecem nos editais do vestibular?", "Editais do Vestibular"),
]


async def run_evaluation(
    mode: str = "compare",
    output: str | Path = "data/exports/evaluation_results.csv",
    max_questions: int | None = None,
    include_baseline: bool = True,
    settings: Settings | None = None,
) -> EvaluationSummary:
    settings = settings or get_settings()
    settings.ensure_dirs()
    service = RagService(settings)
    llm = LLMService(settings)

    questions = QUESTION_SET[: max_questions or len(QUESTION_SET)]
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "question",
                "expected_category",
                "mode",
                "answer",
                "providers",
                "citations",
                "top_score",
                "no_rag_baseline",
            ],
        )
        writer.writeheader()
        for question, expected_category in questions:
            response = await service.answer(ChatRequest(question=question, mode=mode))
            baseline = ""
            if include_baseline:
                baseline_result = await llm.generate("ollama", build_no_rag_prompt(question))
                baseline = baseline_result.answer

            writer.writerow(
                {
                    "question": question,
                    "expected_category": expected_category,
                    "mode": mode,
                    "answer": response.answer,
                    "providers": json.dumps(
                        [provider.model_dump() for provider in response.providers],
                        ensure_ascii=False,
                    ),
                    "citations": json.dumps(
                        [citation.model_dump() for citation in response.citations],
                        ensure_ascii=False,
                    ),
                    "top_score": response.citations[0].score if response.citations else "",
                    "no_rag_baseline": baseline,
                }
            )

    return EvaluationSummary(
        output=str(output_path),
        questions=len(questions),
        mode=mode,
        include_baseline=include_baseline,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia o chatbot RAG da UNIVERSO.")
    parser.add_argument("--mode", choices=["ollama", "cloud", "compare"], default="compare")
    parser.add_argument("--output", default="data/exports/evaluation_results.csv")
    parser.add_argument("--max-questions", type=int, default=None)
    parser.add_argument("--no-baseline", action="store_true")
    args = parser.parse_args()

    summary = asyncio.run(
        run_evaluation(
            mode=args.mode,
            output=args.output,
            max_questions=args.max_questions,
            include_baseline=not args.no_baseline,
        )
    )
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

