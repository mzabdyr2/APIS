"""Schematy danych dla REST API (request/response).

Pydantic robi za nas:
- walidacje typow i ograniczen (np. min_length na wiadomosci),
- serializacje do JSON i z powrotem,
- automatyczna dokumentacje OpenAPI / Swagger w FastAPI.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000, description="Wiadomosc uzytkownika")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    ok: bool
    error: str | None = None
    used_tokens: int = 0
    history_length: int = 0


class SessionInfo(BaseModel):
    session_id: str
    history_length: int
    created_at: float
    last_used_at: float


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[Message]


class ErrorResponse(BaseModel):
    detail: str
