# ClauseIQ — 14-Day Build Plan

RAG-Based Contract & Document Intelligence Platform

**Scope for MVP:** clause-aware chunking → hybrid retrieval + rerank → citation-grounded Q&A → risk-diffing. Skip multi-tenant auth polish and CI/CD gold-plating until Week 2 tail — get a working core before production features.

## Locked Stack

- **Backend:** FastAPI + Celery
- **Vector DB:** Qdrant (Docker) — better filtering docs than Weaviate for solo learning speed
- **Embeddings:** bge-large (open-source, zero API cost while iterating)
- **LLM:** Claude API for synthesis
- **Database:** PostgreSQL + local disk/S3-stub for files (skip R2 until deploy week)
- **Frontend:** Next.js + Tailwind + PDF.js
- **Auth:** skip real auth until Day 11 — hardcode a single org/user first

---

## Week 1 — Ingestion + Retrieval Core

| Day | Focus | Deliverable |
|---|---|---|
| 1 | Repo setup + architecture | Monorepo (`/backend`, `/frontend`), Docker Compose (Postgres + Qdrant), Postgres schema (`orgs, documents, clauses, clause_embeddings, queries, risk_flags`) migrated. **Commit:** schema + docker-compose, not one mega-commit. |
| 2 | Clause-aware chunker (v1) | Script that takes a PDF/DOCX, splits into clauses by section headers/numbering (regex + heuristics), outputs `{text, clause_type, page, section_number}`. Test on 3 sample contracts. |
| 3 | Embedding + ingestion pipeline | Celery task: parse → chunk → embed (bge-large) → upsert to Qdrant with metadata → mark doc "ready" in Postgres. |
| 4 | Upload API + status tracking | FastAPI endpoints: `POST /documents/upload`, `GET /documents/{id}/status`. Async job triggers ingestion. Manual test via curl/Postman. |
| 5 | Hybrid retrieval (BM25 + vector) | Add BM25 index (rank_bm25 or Postgres full-text) alongside Qdrant vector search. Combine + normalize scores. |
| 6 | Reranker integration | Add cross-encoder (e.g. bge-reranker or Cohere rerank) on top-k hybrid results. Benchmark retrieval quality on 5 hand-written test questions per doc. |
| 7 | Buffer / catch-up + eval notes | Fix whatever broke Days 2–6. Log retrieval recall@k manually for your test set — start of your "how do you evaluate retrieval" interview answer. |

---

## Week 2 — Synthesis, Risk-Diffing, Frontend, Ship

| Day | Focus | Deliverable |
|---|---|---|
| 8 | Citation-grounded answer synthesis | Claude API call: strict prompt forcing answers built only from retrieved chunks, citing chunk IDs. Add a guardrail check — reject/flag answers with no valid citation. |
| 9 | Query API + logging | `POST /query` endpoint wiring retrieval → rerank → synthesis. Log every query + retrieved chunks + answer to `queries` table (for eval). |
| 10 | Risk-diffing engine | Pick 1 contract type (e.g. NDA). Store one "standard template," clause-match new uploads by type, Claude compares new vs standard, output severity-scored flags into `risk_flags`. |
| 11 | Frontend: upload + doc list | Next.js pages: upload UI, document list with ingestion status polling. |
| 12 | Frontend: chat + citation highlighting | Chat UI for Q&A, PDF.js viewer, click-citation → jump to highlighted clause location. |
| 13 | Frontend: risk-diff view + basic auth | Risk flags dashboard view. Bare-bones auth (Clerk quick integration or hardcoded JWT) so it's not a single-user toy. |
| 14 | Polish, deploy, resume writeup | Deploy: frontend → Vercel, backend → Railway/Render, Qdrant+Postgres → managed or single Docker host. Write README + finalize resume bullets with real numbers (actual recall@k, latency) instead of placeholders. |

---

## Git Discipline Reminder

Given Team 85's prior evaluation issues (fake/meaningless commits, sole-contributor patterns), for this solo project:

- Commit at the end of each day minimum
- One logical unit of work per commit
- Real, descriptive messages (`feat: add hybrid BM25+vector retrieval`, not `update`)
- This is exactly the kind of solo-buildable repo where clean commit history will get noticed by reviewers/recruiters

---

## Resume Bullets (draft — finalize with real numbers on Day 14)

- Built a multi-tenant RAG platform with hybrid BM25+vector retrieval and cross-encoder reranking, achieving exact clause-level citation grounding for contract Q&A.
- Designed a clause-aware document chunking pipeline (vs naive fixed-window chunking), improving retrieval precision on legal documents.
- Implemented an automated risk-diffing engine comparing uploaded contracts against org-defined standard templates.

## Likely Interview Questions

- Why hybrid search instead of pure vector similarity?
- How do you prevent hallucinated citations?
- How would you evaluate retrieval quality — what metrics (recall@k, MRR)?
- How does your chunking strategy change for a 200-page contract vs a 2-page NDA?
