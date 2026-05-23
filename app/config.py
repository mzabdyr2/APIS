"""Konfiguracja aplikacji wczytywana ze zmiennych srodowiskowych / pliku .env.

Centralizacja konfiguracji to dobra praktyka:
- jedno miejsce na wszystkie 'pokretla' aplikacji,
- latwa zmiana modelu/URL-a bez modyfikacji kodu,
- bezpieczne przechowywanie sekretow (klucze API w .env, ktory jest w .gitignore).
"""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_base_url: str = Field(default="http://localhost:11434/v1")
    llm_api_key: str = Field(default="ollama")
    llm_model: str = Field(default="llama3.2")

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, gt=0)

    max_context_tokens: int = Field(default=3000, gt=0)
    max_history_messages: int = Field(default=20, gt=0)

    system_prompt: str = Field(
        default=(
            "Jestes pomocnym, rzeczowym asystentem AI. "
            "Odpowiadasz krotko, konkretnie i zgodnie z prawda. "
            "Jezeli nie znasz odpowiedzi - przyznaj sie, zamiast zmyslac. "
            "Domyslnie odpowiadasz po polsku, chyba ze uzytkownik pisze w innym jezyku."
        )
    )

    request_timeout: float = Field(default=60.0, gt=0)


settings = Settings()
