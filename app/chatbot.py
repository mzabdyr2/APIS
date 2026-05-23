"""Klasa Chatbot - integruje LLMClient, ConversationMemory i logger.

To 'mozg' aplikacji. Tutaj dzieje sie:
- walidacja zapytan uzytkownika,
- przygotowanie kontekstu (system prompt + przyciecie historii),
- wywolanie modelu,
- obsluga bledow (polaczenie, limit, autoryzacja, bledne odpowiedzi),
- logowanie zapytan, odpowiedzi i bledow (wymaganie 4.5).
"""
from __future__ import annotations

from dataclasses import dataclass

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from app.config import Settings, settings
from app.llm_client import LLMClient
from app.logger_config import setup_logger
from app.memory import ContextOverflowError, ConversationMemory

logger = setup_logger()


@dataclass
class ChatResult:
    """Wynik pojedynczej tury rozmowy - latwy do serializacji w API."""

    reply: str
    ok: bool
    error: str | None = None
    used_tokens: int = 0
    history_length: int = 0


class Chatbot:
    def __init__(
        self,
        cfg: Settings | None = None,
        llm_client: LLMClient | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self.cfg = cfg or settings
        self.llm = llm_client or LLMClient(self.cfg)
        self.memory = ConversationMemory(
            system_prompt=system_prompt or self.cfg.system_prompt,
            max_context_tokens=self.cfg.max_context_tokens,
            max_history_messages=self.cfg.max_history_messages,
        )
        logger.info(
            "Chatbot zainicjalizowany | model=%s | max_ctx=%d tok | max_hist=%d msg",
            self.cfg.llm_model,
            self.cfg.max_context_tokens,
            self.cfg.max_history_messages,
        )

    @property
    def history(self) -> list[dict]:
        return list(self.memory.history)

    def reset(self) -> None:
        self.memory.reset()
        logger.info("Historia rozmowy wyczyszczona")

    def chat(self, user_message: str) -> ChatResult:
        if not user_message or not user_message.strip():
            logger.warning("Otrzymano puste zapytanie")
            return ChatResult(reply="Prosze wpisz wiadomosc.", ok=False, error="empty_input")

        user_message = user_message.strip()
        logger.info("USER: %s", _shorten(user_message))
        self.memory.add_user(user_message)

        try:
            messages, used = self.memory.build_messages()
            logger.debug("Wysylam %d wiadomosci do modelu (%d tokenow)", len(messages), used)
            reply = self.llm.generate(messages)

            if not reply.strip():
                raise ValueError("Model zwrocil pusta odpowiedz")

            self.memory.add_assistant(reply)
            logger.info("ASSISTANT: %s", _shorten(reply))
            return ChatResult(
                reply=reply,
                ok=True,
                used_tokens=used,
                history_length=len(self.memory),
            )

        except ContextOverflowError as exc:
            logger.error("Przekroczono limit kontekstu: %s", exc)
            self.memory.history.pop()
            return ChatResult(
                reply="Twoja wiadomosc jest za dluga - skroc ja albo zresetuj rozmowe.",
                ok=False,
                error="context_overflow",
                history_length=len(self.memory),
            )

        except APITimeoutError:
            logger.error("Timeout polaczenia z modelem")
            self.memory.history.pop()
            return ChatResult(
                reply="Model nie odpowiedzial w wyznaczonym czasie. Sprobuj ponownie.",
                ok=False,
                error="timeout",
                history_length=len(self.memory),
            )

        except APIConnectionError:
            logger.error("Brak polaczenia z serwerem LLM (czy Ollama dziala?)")
            self.memory.history.pop()
            return ChatResult(
                reply="Nie moge polaczyc sie z modelem. Sprawdz czy serwer LLM dziala.",
                ok=False,
                error="connection_error",
                history_length=len(self.memory),
            )

        except AuthenticationError:
            logger.error("Zly klucz API")
            self.memory.history.pop()
            return ChatResult(
                reply="Blad uwierzytelnienia w API modelu.",
                ok=False,
                error="auth_error",
                history_length=len(self.memory),
            )

        except RateLimitError:
            logger.error("Przekroczono limit zapytan do API")
            self.memory.history.pop()
            return ChatResult(
                reply="Przekroczono limit zapytan do modelu. Poczekaj chwile.",
                ok=False,
                error="rate_limit",
                history_length=len(self.memory),
            )

        except BadRequestError as exc:
            logger.error("Bledne zapytanie do modelu: %s", exc)
            self.memory.history.pop()
            return ChatResult(
                reply="Zapytanie zostalo odrzucone przez model (mozliwe przekroczenie kontekstu).",
                ok=False,
                error="bad_request",
                history_length=len(self.memory),
            )

        except APIStatusError as exc:
            logger.error("Blad API (HTTP %s): %s", exc.status_code, exc)
            self.memory.history.pop()
            return ChatResult(
                reply=f"Blad serwera modelu (HTTP {exc.status_code}).",
                ok=False,
                error=f"api_error_{exc.status_code}",
                history_length=len(self.memory),
            )

        except APIError as exc:
            logger.error("Inny blad biblioteki OpenAI: %s", exc)
            self.memory.history.pop()
            return ChatResult(
                reply="Nieoczekiwany blad po stronie modelu.",
                ok=False,
                error="api_error",
                history_length=len(self.memory),
            )

        except ValueError as exc:
            logger.error("Niepoprawna odpowiedz modelu: %s", exc)
            self.memory.history.pop()
            return ChatResult(
                reply="Model zwrocil nieprawidlowa odpowiedz.",
                ok=False,
                error="invalid_response",
                history_length=len(self.memory),
            )

        except Exception as exc:
            logger.exception("Nieprzewidziany blad: %s", exc)
            self.memory.history.pop()
            return ChatResult(
                reply="Wystapil nieoczekiwany blad.",
                ok=False,
                error="unknown",
                history_length=len(self.memory),
            )


def _shorten(text: str, limit: int = 120) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


if __name__ == "__main__":
    bot = Chatbot()
    result = bot.chat("Czesc, kim jestes?")
    print(result.reply)
    print(f"\nLog: ok={result.ok}, tokens={result.used_tokens}, history={result.history_length}")
