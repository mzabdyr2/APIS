# Production Ready Chatbot

Chatbot oparty o LLM z REST API, obsługą sesji, kontrolą długości kontekstu
i pełnym logowaniem. Projekt na przedmiot **Aktualne Problemy Informatyki
Stosowanej** (Geoinformatyka II st.) – Zadanie 3.

## Struktura projektu

```
.
├── app/                     # Kod aplikacji
│   ├── chatbot.py           # Klasa Chatbot - logika dialogu
│   ├── llm_client.py        # Warstwa komunikacji z modelem LLM
│   ├── memory.py            # Historia + kontrola długości kontekstu (tokeny)
│   ├── session_manager.py   # Wiele sesji równolegle
│   ├── schemas.py           # Modele Pydantic dla API
│   ├── main.py              # Aplikacja FastAPI (REST)
│   ├── logger_config.py     # Konfiguracja logowania
│   └── config.py            # Ustawienia (z .env)
├── notebooks/
│   ├── 01_demo_chatbot.ipynb   # Demonstracja klasy Chatbot
│   └── 02_demo_api.ipynb       # Demonstracja REST API
├── logs/                    # Pliki logów (tworzone automatycznie)
├── sprawozdanie.md          # Sprawozdanie - źródło (Markdown)
├── sprawozdanie.pdf         # Sprawozdanie - wersja do wysłania
├── requirements.txt         # Zależności Pythona
├── .env.example             # Szablon konfiguracji
└── README.md
```

## Szybki start

### 1. Instalacja zależności

```bash
python3 -m pip install -r requirements.txt
```

### 2. Uruchomienie modelu LLM (lokalnie przez Ollamę)

W osobnym terminalu:
```bash
ollama serve
ollama pull llama3.2
```

### 3. Konfiguracja (opcjonalnie)

```bash
cp .env.example .env
# edytuj .env według potrzeb (model, parametry, limity)
```

### 4. Uruchomienie

**Wariant A – API (REST):**
```bash
uvicorn app.main:app --reload
# Dokumentacja: http://localhost:8000/docs
```

**Wariant B – z poziomu Pythona:**
```python
from app.chatbot import Chatbot
bot = Chatbot()
result = bot.chat("Cześć, kim jesteś?")
print(result.reply)
```

**Wariant C – notebooki demonstracyjne:**
```bash
jupyter notebook notebooks/
```

## Przykładowe wywołania API

```bash
# Health
curl http://localhost:8000/health

# Utworzenie sesji
SID=$(curl -s -X POST http://localhost:8000/sessions | python3 -c "import sys,json;print(json.load(sys.stdin)['session_id'])")

# Wysłanie wiadomości
curl -X POST http://localhost:8000/sessions/$SID/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Cześć, jak masz na imię?"}'

# Historia
curl http://localhost:8000/sessions/$SID/history

# Usunięcie sesji
curl -X DELETE http://localhost:8000/sessions/$SID
```

## Spełnione wymagania

| Ocena | Wymaganie |
|---|---|
| 3.5 | Klasa, prompt systemowy, historia, parametry generacji, integracja z LLM |
| 4.0 | Kontrola długości kontekstu (sliding window po tokenach) |
| 4.5 | Pełna obsługa błędów + logowanie do plików |
| 5.0 | REST API w FastAPI + obsługa sesji użytkownika (UUID4) |

Szczegóły w `sprawozdanie.pdf`.

## Konfiguracja

Wszystkie parametry można zmieniać przez plik `.env` lub zmienne środowiskowe.
Najważniejsze:

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | URL serwera LLM |
| `LLM_MODEL` | `llama3.2` | Nazwa modelu |
| `TEMPERATURE` | `0.7` | Kreatywność (0-2) |
| `TOP_P` | `0.9` | Nucleus sampling |
| `MAX_TOKENS` | `1024` | Limit długości odpowiedzi |
| `MAX_CONTEXT_TOKENS` | `3000` | Okno kontekstu (tokenów) |
| `MAX_HISTORY_MESSAGES` | `20` | Limit liczby wiadomości w historii |
