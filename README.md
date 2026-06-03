# GRC MVP

Automates security questionnaire responses using your existing policies and past answers.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (`pip install uv` or `curl -Ls https://astral.sh/uv/install.sh | sh`)
- Docker Desktop (for Postgres + pgvector)

## Setup

### 1. Clone and enter the project

```bash
cd grc-mvp
```

### 2. Create virtual environment and install dependencies

```bash
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY and OPENAI_API_KEY
```

### 4. Start the database

```bash
docker compose up -d
```

Wait for the healthcheck to pass (`docker compose ps` shows `healthy`).

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the dev server

```bash
uvicorn app.main:app --reload
```

App is at http://localhost:8000

## Project layout

```
app/
  main.py            FastAPI entry point
  config.py          Environment variable loading
  db.py              SQLAlchemy engine + session
  models.py          ORM models: KnowledgeChunk, Questionnaire, Question
  routes/
    auth.py          Register, login, JWT cookies
    api.py           JSON API for React frontend (questionnaires, knowledge, export, …)
    admin.py         Internal admin endpoints
  services/
    parsing.py       PDF / DOCX / XLSX parsers       (Phase 2)
    embeddings.py    Embedding generation             (Phase 2)
    retrieval.py     pgvector similarity search       (Phase 4)
    generation.py    Claude API prompting             (Phase 4)
  templates/         Jinja2 + HTMX HTML templates
tests/               pytest test suite
migrations/          Alembic migration scripts
```

## Running tests

```bash
pytest
```

## Product features (current)

- Multi-sheet Excel upload with column mapping
- Background AI answer generation with progress polling
- Optional questionnaire due dates and email reminders
- Email verification required for upload / generate (skipped when `TESTING=true`)
- Answer library, knowledge base (RAG), audit log, trash with 90-day auto-purge
- Consultant vs company workspace modes

## Build phases (historical)

| Phase | Feature |
|-------|---------|
| 1 | Project scaffold |
| 2 | Knowledge base ingestion |
| 3 | Questionnaire upload + parsing |
| 4 | AI answer generation |
| 5 | Review interface + Excel export |
