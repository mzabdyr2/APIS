"""Pamiec rozmowy z kontrola dlugosci kontekstu (wymaganie na ocene 4.0).

Strategia:
- Przechowujemy pelna historie wiadomosci (lista slownikow {role, content}).
- Przy budowaniu promptu dla modelu stosujemy 'sliding window' po tokenach:
  bierzemy najnowsze wiadomosci tak, by ich laczna liczba tokenow miescila sie
  w `max_context_tokens`. System prompt jest zawsze wlaczany jako pierwszy.
- Do liczenia tokenow uzywamy `tiktoken`. Ollama / Llama uzywaja innego tokenizera
  niz OpenAI, ale dla celow ograniczania kontekstu wystarczy estymacja - rzad
  wielkosci jest taki sam, a kazdy 'realny' tokenizer wymagalby ladowania modelu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import tiktoken

Role = Literal["system", "user", "assistant"]

_ENCODER = tiktoken.get_encoding("cl100k_base")
_TOKENS_PER_MESSAGE_OVERHEAD = 4


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(_ENCODER.encode(text))


def count_message_tokens(message: dict) -> int:
    return count_tokens(message.get("content", "")) + _TOKENS_PER_MESSAGE_OVERHEAD


class ContextOverflowError(Exception):
    """Wyrzucany gdy sama wiadomosc uzytkownika + system prompt nie miesci sie w oknie."""


@dataclass
class ConversationMemory:
    system_prompt: str
    max_context_tokens: int = 3000
    max_history_messages: int = 20
    history: list[dict] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        self.history.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.history.append({"role": "assistant", "content": content})

    def reset(self) -> None:
        self.history.clear()

    def __len__(self) -> int:
        return len(self.history)

    def build_messages(self) -> tuple[list[dict], int]:
        """Buduje liste wiadomosci do wyslania do modelu.

        Zwraca krotke: (lista_wiadomosci, liczba_uzytych_tokenow).
        """
        system_msg = {"role": "system", "content": self.system_prompt}
        system_tokens = count_message_tokens(system_msg)
        budget = self.max_context_tokens - system_tokens

        if budget <= 0:
            raise ContextOverflowError(
                "System prompt sam przekracza limit kontekstu - zwieksz max_context_tokens "
                "albo skroc system_prompt."
            )

        trimmed: list[dict] = []
        used = 0
        for msg in reversed(self.history[-self.max_history_messages:]):
            cost = count_message_tokens(msg)
            if used + cost > budget:
                break
            trimmed.append(msg)
            used += cost
        trimmed.reverse()

        if not trimmed and self.history:
            last = self.history[-1]
            raise ContextOverflowError(
                f"Ostatnia wiadomosc ma {count_message_tokens(last)} tokenow, "
                f"a dostepny budzet to {budget}. Skroc zapytanie."
            )

        return [system_msg] + trimmed, system_tokens + used
