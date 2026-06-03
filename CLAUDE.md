# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Greenlight — an AI-powered security questionnaire automation tool for SMB SaaS companies and GRC consultants. Users upload policy documents and past questionnaires; the system uses RAG to auto-generate answers for new questionnaires, which analysts review and export as filled Excel files.

## Tech stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL with pgvector (port 5434)
- **Frontend**: React 19 + Vite + Tailwind CSS 4 (port 5173, proxies `/api/*` to `:8000`)
- **AI**: Multi-provider LLM (Gemini 2.5 Flash primary, Groq/Cerebras/OpenRouter free-tier fallbacks, Anthropic as option) + Voyage AI embeddings (`voyage-3`, 1024-dim)
- **Auth**: JWT in HttpOnly cookies (`greenlight_token`), Argon2id hashing (bcrypt legacy migration supported), 7-day expiry
- **Package manager**: `uv` (not pip directly)

## Development commands

```bash
# Start DB
docker compose up -d

# Run backend (from project root, venv activated)
uvicorn app.main:app --reload

# Run frontend (separate terminal)
cd frontend && npm run dev

# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Run all tests
pytest

# Run a single test file
pytest tests/test_critical_path.py -v

# Run a single test
pytest tests/test_critical_path.py::test_name -v

# Install dependencies
uv pip install -e ".[dev]"
```

## Architecture

### Multi-tenant model

Every resource (documents, questionnaires, answers) belongs to a `Workspace` (tenant). Users belong to one workspace. Roles: `owner` | `admin` | `member`. All DB queries must filter by `workspace_id` — never return cross-workspace data.

`Workspace.workspace_type` is either `"consultant"` or `"company"`, distinguishing GRC consultants managing multiple clients from companies managing their own compliance.

### RAG pipeline

The retrieval pipeline (`app/services/retrieval.py`) has 8 layers:
1. HyDE + query expansion (one LLM call → hypothetical answer + 3 rephrasings)
2. Multi-vector dense search (pgvector for each query variant)
3. PostgreSQL full-text search (GIN index)
4. Reciprocal Rank Fusion (merges all ranked lists)
5. Source type boosting (`approved_answer` +35%)
6. Per-workspace feedback scoring (approve/reject history)
7. Voyage reranking (`rerank-2`, top-20 candidates)
8. Deduplication (cosine ≥ 0.92 threshold)

Every layer degrades gracefully — failure falls back to previous layer's output.

### Multi-client answer isolation

`KnowledgeChunk.customer_name` and `ApprovedAnswer.customer_name` are `NULL` for generic answers (reused across all clients) and set to the customer name for client-specific answers. The RAG SQL filter uses this to return both generic + client-specific chunks while excluding other clients' answers.

### LLM provider cascade

`app/services/generation.py` tries providers in priority order (quality vs. quota). A `429` marks a provider exhausted for 24 hours. A `503` retries the same provider 3× with 10s gaps before skipping. Provider priority: Gemini 2.5 Flash → Gemma 3 27B → Groq Llama 3.3 70B → Groq Llama 4 Scout → Cerebras → Groq 8B → OpenRouter fallbacks.

### Job queue

Background tasks (emails etc.) go through a Postgres-backed `job_queue` table, not FastAPI `BackgroundTasks`. The worker loop (`app/services/jobs.py`) runs as an asyncio task in the lifespan and polls every 10 seconds. Use `jobs.enqueue(job_type, payload)` to add jobs.

### Answer library

`ApprovedAnswer` table stores approved answers with embeddings of the question text. When generating answers for new questionnaires, similarity search against this table surfaces reusable answers before hitting the full RAG pipeline. `detect_category()` uses keyword matching; `classify_category()` uses embedding similarity against anchor sentences.

### Frontend API layer

All frontend→backend calls go through `frontend/src/api.js` — a thin wrapper with `credentials: 'include'` on every request. On 401, it redirects to `/login`. Auth state lives in `AuthContext.jsx`. React Router is used for client-side routing.

### File storage

Questionnaire XLSX files: stored in Postgres as `LargeBinary` (legacy, `raw_xlsx_blob`) or in S3-compatible storage (`raw_xlsx_key`). Set `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT_URL` in `.env` to use S3/R2/MinIO. If blank, falls back to Postgres.

## Key files

| File | Purpose |
|------|---------|
| `app/models.py` | All ORM models — read this first when understanding data shapes |
| `app/config.py` | All env vars via pydantic-settings — `get_settings()` is cached |
| `app/routes/api.py` | Main JSON API router for the React frontend |
| `app/services/retrieval.py` | 8-layer RAG pipeline |
| `app/services/generation.py` | LLM provider cascade + answer generation |
| `app/auth.py` | JWT + password hashing (Argon2id / bcrypt migration) |
| `migrations/versions/` | Alembic migration chain — check `alembic history` before adding |

## Testing

Tests use the real Postgres DB wrapped in transactions that roll back after each test — no test data persists. All LLM and embedding calls are mocked (`unittest.mock.patch`). The DB fixture overrides FastAPI's `get_db` dependency.

```bash
pytest tests/test_critical_path.py  # full flow: register → upload → generate → approve → export
pytest tests/test_retrieval.py      # RAG pipeline
pytest tests/test_generation.py     # LLM provider logic
```

## Required `.env` keys

```
DATABASE_URL=postgresql://grc:grc_secret@localhost:5434/grc_db
JWT_SECRET_KEY=<any long random string>
ANTHROPIC_API_KEY=<optional, for Anthropic provider>
GEMINI_API_KEY=<primary LLM>
VOYAGE_API_KEY=<embeddings — required for production>
OPENAI_API_KEY=<fallback embeddings>
```

All other keys (`GROQ_API_KEY`, `CEREBRAS_API_KEY`, `RESEND_API_KEY`, `S3_*`, `SENTRY_DSN`) are optional.
