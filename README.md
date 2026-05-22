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
    knowledge.py     Upload policies / past answers  (Phase 2)
    questionnaires.py Upload + list questionnaires   (Phase 3)
    answers.py       Generate, review, export        (Phases 4–5)
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

## Build phases

| Phase | Feature |
|-------|---------|
| 1 | Project scaffold (this) |
| 2 | Knowledge base ingestion |
| 3 | Questionnaire upload + parsing |
| 4 | AI answer generation |
| 5 | Review interface + Excel export |
