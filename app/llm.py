from __future__ import annotations

import time

import httpx

from app.config import Settings
from app.schemas import ProviderAnswer


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, provider: str, prompt: str) -> ProviderAnswer:
        if provider == "cloud":
            return await self._generate_cloud(prompt)
        return await self._generate_ollama(prompt)

    async def _generate_ollama(self, prompt: str) -> ProviderAnswer:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                    json={
                        "model": self.settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                response.raise_for_status()
                answer = response.json().get("response", "").strip()
        except Exception as exc:
            answer = "Ollama indisponivel. Verifique se o modelo foi baixado no container."
            return ProviderAnswer(
                provider="ollama",
                answer=answer,
                latency_ms=_elapsed_ms(start),
                error=str(exc),
            )

        return ProviderAnswer(provider="ollama", answer=answer, latency_ms=_elapsed_ms(start))

    async def _generate_cloud(self, prompt: str) -> ProviderAnswer:
        start = time.perf_counter()
        if not self.settings.cloud_api_key or not self.settings.cloud_model:
            return ProviderAnswer(
                provider="cloud",
                answer="Modo cloud nao configurado. Defina CLOUD_API_KEY e CLOUD_MODEL.",
                latency_ms=_elapsed_ms(start),
                error="cloud_not_configured",
            )

        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.cloud_api_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.cloud_api_key}"},
                    json={
                        "model": self.settings.cloud_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Voce responde em portugues do Brasil e usa somente as fontes fornecidas.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                answer = payload["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return ProviderAnswer(
                provider="cloud",
                answer="API em nuvem indisponivel ou mal configurada.",
                latency_ms=_elapsed_ms(start),
                error=str(exc),
            )

        return ProviderAnswer(provider="cloud", answer=answer, latency_ms=_elapsed_ms(start))


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

