"""REST API udostepniajace chatbota jako uslugi (wymaganie na ocene 5.0).

Uruchomienie:
    uvicorn app.main:app --reload

Dokumentacja interaktywna automatycznie pod:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logger_config import setup_logger
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    Message,
    SessionInfo,
)
from app.session_manager import SessionManager, SessionNotFoundError

logger = setup_logger()

app = FastAPI(
    title="Production Ready Chatbot",
    description=(
        "Chatbot oparty o LLM z obsluga sesji uzytkownikow, kontrola "
        "dlugosci kontekstu i pelnym logowaniem."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_session_manager = SessionManager(cfg=settings)


def get_session_manager() -> SessionManager:
    return _session_manager


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "model": settings.llm_model}


@app.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
    tags=["sessions"],
    summary="Utworz nowa sesje rozmowy",
)
def create_session(sm: SessionManager = Depends(get_session_manager)) -> dict:
    session_id = sm.create()
    return {"session_id": session_id}


@app.get("/sessions", tags=["sessions"], summary="Lista aktywnych sesji")
def list_sessions(sm: SessionManager = Depends(get_session_manager)) -> dict:
    return {"sessions": sm.list_ids()}


@app.get(
    "/sessions/{session_id}",
    tags=["sessions"],
    summary="Informacje o sesji",
    response_model=SessionInfo,
)
def get_session(
    session_id: str,
    sm: SessionManager = Depends(get_session_manager),
) -> SessionInfo:
    try:
        s = sm.info(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")
    return SessionInfo(
        session_id=session_id,
        history_length=len(s.bot.memory),
        created_at=s.created_at,
        last_used_at=s.last_used_at,
    )


@app.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["sessions"],
    summary="Usun sesje",
)
def delete_session(
    session_id: str,
    sm: SessionManager = Depends(get_session_manager),
) -> None:
    try:
        sm.delete(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")


@app.get(
    "/sessions/{session_id}/history",
    tags=["sessions"],
    summary="Pobierz historie rozmowy",
    response_model=HistoryResponse,
)
def get_history(
    session_id: str,
    sm: SessionManager = Depends(get_session_manager),
) -> HistoryResponse:
    try:
        bot = sm.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")
    return HistoryResponse(
        session_id=session_id,
        messages=[Message(**m) for m in bot.history],
    )


@app.post(
    "/sessions/{session_id}/chat",
    tags=["chat"],
    summary="Wyslij wiadomosc w ramach sesji",
    response_model=ChatResponse,
)
def chat(
    session_id: str,
    request: ChatRequest,
    sm: SessionManager = Depends(get_session_manager),
) -> ChatResponse:
    try:
        bot = sm.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Sesja nie istnieje")

    result = bot.chat(request.message)
    return ChatResponse(
        session_id=session_id,
        reply=result.reply,
        ok=result.ok,
        error=result.error,
        used_tokens=result.used_tokens,
        history_length=result.history_length,
    )
