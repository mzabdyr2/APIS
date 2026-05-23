"""Warstwa komunikacji z modelem jezykowym.

Uzywamy klienta OpenAI w wersji 'OpenAI-compatible' - dziala on zarowno z:
- Ollama (lokalnie, base_url=http://localhost:11434/v1),
- OpenAI (https://api.openai.com/v1),
- innymi serwerami zgodnymi z protokolem (vLLM, LM Studio, llama.cpp server, ...).

Dzieki temu warstwa logiczna (Chatbot) nie wie skad pochodzi model - to klasyczny
przyklad wzorca 'wrapper / adapter'.
"""
from __future__ import annotations

from typing import Iterable

from openai import OpenAI

from app.config import Settings, settings


class LLMClient:
    def __init__(self, cfg: Settings | None = None) -> None:
        self.cfg = cfg or settings
        self._client = OpenAI(
            base_url=self.cfg.llm_base_url,
            api_key=self.cfg.llm_api_key,
            timeout=self.cfg.request_timeout,
        )

    def generate(self, messages: Iterable[dict]) -> str:
        """Wysyla liste wiadomosci do modelu i zwraca tresc odpowiedzi.

        Parametry generacji pochodza z konfiguracji:
        - temperature: kreatywnosc (0 = deterministyczne, 1+ = kreatywne / halucynacje)
        - top_p: nucleus sampling, ograniczamy do najbardziej prawdopodobnych tokenow
        - max_tokens: gorny limit dlugosci odpowiedzi (chroni przed niekonczacymi sie
          odpowiedziami i kosztami).

        Specjalnie NIE lapiemy tu wyjatkow - chcemy zeby Chatbot mogl je obsluzyc
        i zalogowac w sposob dopasowany do kontekstu (single responsibility).
        """
        response = self._client.chat.completions.create(
            model=self.cfg.llm_model,
            messages=list(messages),
            temperature=self.cfg.temperature,
            top_p=self.cfg.top_p,
            max_tokens=self.cfg.max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""


if __name__ == "__main__":
    client = LLMClient()
    test = [{"role": "user", "content": "Powiedz krotko: dziala."}]
    print(client.generate(test))
