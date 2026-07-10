# ClauseIQ

RAG-based contract & document intelligence platform. Upload contracts (PDF/DOCX), ask natural-language questions across one or many documents, get answers with exact clause citations, plus automated risk-flagging against a standard template.

## Stack

- **Backend:** FastAPI + Celery
- **Vector DB:** Qdrant
- **Embeddings:** bge-large
- **LLM:** Claude API
- **Database:** PostgreSQL
- **Frontend:** Next.js + Tailwind + PDF.js

## Setup

### 1. Start infrastructure
```bash
docker compose up -d
```
This brings up Postgres (`localhost:5432`) and Qdrant (`localhost:6333`).

### 2. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run migrations
```bash
alembic upgrade head
```

### 4. Start the API
```bash
uvicorn app.main:app --reload
```

Check it's alive:
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Project Structure

```
clauseiq/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   │   └── db.py        # SQLAlchemy models: orgs, documents, clauses, etc.
│   │   ├── services/
│   │   └── workers/         # Celery tasks (ingestion pipeline)
│   ├── migrations/           # Alembic migrations
│   └── requirements.txt
└── frontend/                 # Next.js app
```

## Status

Day 1 of 14 — infra + schema scaffolded. See build plan for full roadmap.
