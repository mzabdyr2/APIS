"""Mened\u017cer sesji - przechowuje wielu uzytkownikow rownoczesnie.

Kazda sesja to jeden niezalezny Chatbot z wlasna historia rozmowy.
Identyfikator (session_id) jest UUID4 - przekazujemy go w API i klient
uzywa tego samego ID przy kolejnych wiadomosciach.

Implementacja: in-memory (slownik) z mechanizmem TTL (auto-czyszczenie
stalych sesji). W produkcji mozna zamienic na Redis bez zmian w API.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass

from app.chatbot import Chatbot
from app.config import Settings, settings
from app.logger_config import setup_logger

logger = setup_logger()


@dataclass
class Session:
    bot: Chatbot
    created_at: float
    last_used_at: float


class SessionNotFoundError(KeyError):
    """Rzucany gdy klient poda nieistniejacy / wygasly session_id."""


class SessionManager:
    def __init__(self, cfg: Settings | None = None, ttl_seconds: float = 3600) -> None:
        self.cfg = cfg or settings
        self.ttl = ttl_seconds
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, system_prompt: str | None = None) -> str:
        session_id = str(uuid.uuid4())
        bot = Chatbot(cfg=self.cfg, system_prompt=system_prompt)
        now = time.time()
        with self._lock:
            self._sessions[session_id] = Session(bot=bot, created_at=now, last_used_at=now)
        logger.info("Utworzono sesje %s", session_id)
        return session_id

    def get(self, session_id: str) -> Chatbot:
        self._sweep_expired()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            session.last_used_at = time.time()
            return session.bot

    def info(self, session_id: str) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError(session_id)
            return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info("Usunieto sesje %s", session_id)
            else:
                raise SessionNotFoundError(session_id)

    def list_ids(self) -> list[str]:
        self._sweep_expired()
        with self._lock:
            return list(self._sessions.keys())

    def _sweep_expired(self) -> None:
        cutoff = time.time() - self.ttl
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.last_used_at < cutoff]
            for sid in expired:
                del self._sessions[sid]
        if expired:
            logger.info("Usunieto %d wygaslych sesji", len(expired))
