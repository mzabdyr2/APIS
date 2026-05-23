# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Python FastAPI chatbot with LLM integration via OpenAI-compatible API. See `README.md` for full setup and API usage examples.

### Services

| Service | Command | Port | Notes |
|---|---|---|---|
| **Ollama** (LLM backend) | `ollama serve` | 11434 | Must be running before the FastAPI app can handle `/chat` requests. Pull model first: `ollama pull llama3.2` |
| **FastAPI app** | `uvicorn app.main:app --reload` | 8000 | Swagger docs at `http://localhost:8000/docs` |

### Running the app

1. Start Ollama in background: `ollama serve &` (or in a separate tmux session)
2. Ensure model is pulled: `ollama pull llama3.2` (no-op if already present)
3. Start dev server: `uvicorn app.main:app --reload`
4. Health check: `curl http://localhost:8000/health`

### Gotchas

- **No test suite exists** in the repo. Verify changes by running the API and testing endpoints manually via `curl` or the Swagger UI at `/docs`.
- **No linter/formatter** is configured. There are no `pyproject.toml`, `setup.cfg`, or linting scripts.
- **`.env` file required**: Copy `.env.example` to `.env` before starting the app. Defaults point to local Ollama on port 11434.
- **Ollama model download**: `ollama pull llama3.2` downloads ~2 GB on first run. Subsequent calls are no-ops.
- **System prompt is in Polish by default** (configured in `app/config.py`). The chatbot responds in Polish unless the user writes in another language.
- **In-memory sessions**: All sessions are lost when the FastAPI process restarts.
- **Logs directory**: Created automatically at `logs/` with `chatbot.log` and `errors.log`.
