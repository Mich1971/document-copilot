# Document Copilot — implementation checklist

Work top to bottom. Each phase unlocks the next. Check items off as you go.

## Where to start: backend, frontend, or both?

**Start with foundation, then backend-led vertical slices.**


| Order                             | Why                                                                                                                    |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1. Supabase + sample data         | Everything persists here; you need a project and a corpus to test against.                                             |
| 2. Backend schema + migrations    | Auth, chat, retrieval, and citations all depend on the data model.                                                     |
| 3. Thin vertical slices           | Wire auth, then a stubbed chat stream, then real RAG — each slice touches frontend + backend together.                 |
| 4. Frontend in parallel (lightly) | Scaffold the SPA early, but don't build citation UI or chat polish until the backend can return real grounded answers. |


The critical path is **data model → ingestion → retrieval → LLM → citations**. The frontend is mostly a streaming chat shell with auth and citation display — it shouldn't get far ahead of working APIs.

---



## Phase 0 — Prerequisites & foundation

- [x] Install toolchain: Python 3.12+, `uv`, Node 20+, `pnpm` (see [README](../README.md))
- [x] Create Supabase project and collect credentials ([supabase-setup](guides/supabase-setup.md))
- [x] Create OpenAI API key (needed from Phase 6 onward)
- [x] Corpus: se usaron PDFs locales en `data/downloads/` (12 documentos) en vez del corpus SEC 10-K

---



## Phase 1 — Backend scaffold & database

Goal: a running FastAPI service with a migrated Supabase schema.

- [x] Init backend deps and project layout ([backend-setup](guides/backend-setup.md))
- [x] `app/config.py` — settings module, fail fast on missing env vars
- [x] `app/main.py` — FastAPI app, CORS, health check (`GET /health`)
- [x] SQLAlchemy models in `app/database/models/`:
  - [x] `users`
  - [x] `source_documents`
  - [x] `document_chunks` (embedding + generated `tsvector`)
  - [x] `chat_threads`
  - [x] `chat_messages`
  - [x] `message_citations`
- [x] Alembic init + first migration:
  - [x] `create extension if not exists vector`
  - [x] `vector(1536)` embedding column
  - [x] generated `tsvector` column on chunks
  - [x] HNSW index (`vector(1536)` en migraci�n inicial; luego migrado a `vector(2048)` con �ndice funcional `halfvec(2048)` para soportar >2000 dims)
  - [x] Recrear columna search_vector (tsvector) + GIN index; se perdió en migración 2c718e53341 (migración 5854003476ac)
  - [x] RLS policies (users see only their own chats)
- [x] `uv run alembic upgrade head` against Supabase direct connection
- [x] `app/database/supabase.py` — user-scoped and service-role clients
- [x] Verify: `uv run uvicorn app.main:app --reload` → health check returns 200

---



## Phase 2 — Auth (full stack)

Goal: analysts can sign in with email; backend rejects unauthenticated requests.

**Backend**

- [x] `app/auth/dependencies.py` — verify `Authorization: Bearer <supabase_jwt>`, expose `get_current_user`
- [x] Reject missing/expired tokens with `401` before any chat or retrieval work

**Frontend**

- [x] Scaffold Vite + React + TypeScript + Tailwind + shadcn ([frontend-setup](guides/frontend-setup.md))
- [x] `src/lib/env.ts` — validate `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- [x] `src/lib/supabase.ts` — browser Supabase client
- [x] `src/lib/http.ts` + `src/lib/api.ts` — fetch wrapper with automatic bearer token
- [x] Sign-in / sign-up pages (email only, no SSO)
- [x] Protected routes — redirect unauthenticated users to login
- [x] Verify: sign up, sign in, token reaches backend on a test authenticated endpoint

---



## Phase 3 — Chat shell (vertical slice, stubbed)

Goal: end-to-end chat UI streaming from FastAPI, no real retrieval yet.

**Backend**

- [x] Chat thread CRUD: list threads, create thread, load message history
- [x] `POST /chats/stream` — accepts AI SDK message format, streams a stubbed assistant reply
- [x] Persist user + assistant messages to `chat_messages` after stream completes
- [x] `403` when user accesses another user's thread

**Frontend**

- [x] React Router: login, chat list, chat thread routes
- [x] AI SDK chat primitives pointed at `POST /chats/stream` with Supabase bearer token
- [x] Thread sidebar (past conversations)
- [x] Basic message list + input + streaming indicator
- [x] Verify: create thread, send message, see streamed stub response, reload and see history

---



## Phase 4 � Ingestion pipeline

Goal: documents in the corpus are parsed, chunked, embedded, and stored in Supabase.

- [x] data/convert_pdfs_to_docling.py � PDF ? DoclingDocument JSON pipeline
- [x] data/doclingdocuments/manifest.json � conversion manifest for UI-driven ingestion
- [x] uploaded_documents table + SQLAlchemy model for locally uploaded PDFs
- [x] Alembic migration 2c718e53341_add_uploaded_documents (includes uploaded_documents + document_tables)
- [x] Ingestion API routes: GET/POST /ingest/documents, PATCH /ingest/documents/{id}
- [x] Chunking strategy: Docling HybridChunker (max 800 tokens), page/section metadata
- [x] Write source_documents rows con metadata de documentos locales
- [x] Write document_chunks rows con text + metadata + embeddings
- [x] OpenRouter embedding generation (`nvidia/nemotron-3-embed-1b:free`) → `vector(2048)` per chunk
- [x] Recrear search_vector (tsvector) + GIN index (migración 5854003476ac, config spanish)
- [x] Idempotent re-run: comportamiento **replace** por documento (borra chunks anteriores, inserta nuevos)
- [x] Unit tests: chunking logic, metadata extraction (tests/ingest/test_chunking.py, 5 tests)
- [x] Run ingestion on sample corpus (12 PDFs locales)
- [x] Verify: 60 chunks con embeddings de 2048 dims en Supabase; smoke test de 1 chunk exitoso
- [x] �ndice HNSW funcional ix_document_chunks_embedding_hnsw_halfvec sobre CAST(embedding AS halfvec(2048)) para superar l�mite de pgvector 0.8.x con >2000 dims

---



## Phase 5 — Retrieval

Goal: a user question returns ranked, relevant source passages.

- [x] `retrieval/queries.py` — pgvector semantic search over `document_chunks`
- [x] `retrieval/queries.py` — Postgres full-text search over `search_vector` (spanish config)
- [x] `retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [x] `retrieval/retriever.py` — query → fused ranked passages + neighbor chunks
- [x] Unit tests: fusion ranking, query assembly (mock DB) (tests/retrieval/, 12 tests)
- [ ] Integration test (optional, `@pytest.mark.integration`): real query against ingested corpus
- [ ] Verify: test queries from client brief return relevant chunks (user provides questions when required)

---



## Phase 6 — LLM agent & grounding

Goal: grounded answers with enforced citations — the core product contract.

- [x] `assistant/instructions.md` — product contract (cite everything, refuse to invent, no stock picks)
- [x] PydanticAI agent with typed deps (`DocumentAgentDeps`) and output (`GroundedAnswer`)
- [x] Agent tools: `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [x] `chat/orchestrator.py` — one turn: retrieve → agent → validate → stream → persist
- [x] `grounding/validator.py` — every citation maps to a retrieved passage; fail closed on violation
- [x] `chat/streaming.py` — AI SDK-compatible stream (text deltas + citation metadata parts)
- [x] Persist `message_citations` linked to assistant messages
- [x] Unit tests: citation validation, grounding enforcement, message conversion (tests/assistant/, tests/grounding/, tests/chat/, 24 tests)
- [ ] Verify against [client-brief example questions](client-brief.md#example-analyst-questions):
  - [ ] Answers cite specific filings and pages
  - [ ] Under-specified questions get "not enough evidence" responses
  - [ ] Question 10 (generative AI margins) refuses to infer beyond filings

---



## Phase 7 — Trust UI (citations & source passages)

Goal: analysts can verify every claim in one click — this is what makes the product usable.

- [ ] Citation chips/links on assistant messages (company, filing type, date, page/section)
- [ ] Source passage panel — show underlying excerpt for selected citation
- [ ] Empty states (no threads, no corpus match)
- [ ] Error states (auth expired, retrieval failure, grounding failure, network/CORS)
- [ ] Loading/streaming status during assistant run
- [ ] Verify: click a citation → see the exact passage from the filing

---



## Phase 8 — Pilot readiness

Goal: 5 senior analysts can use it for a week and report ≥3 hours saved per analyst per week.

- [ ] README "Running locally" section — copy-paste commands for backend + frontend + env vars
- [ ] Seed or document how to ingest/update the corpus
- [ ] Smoke-test all 10 example questions from the client brief
- [ ] Confirm chat history persists across sessions
- [ ] Confirm ~40-user scale assumptions (no hardcoded single-user shortcuts)
- [ ] Basic structured logging on backend (`structlog`) for debugging failed turns
- [ ] Review latency: streaming starts within a few seconds for typical queries

---



## Phase 9 — Deployment (OCI)

- [ ] OCI: backend service (Uvicorn, env vars, `ALLOWED_ORIGINS`)
- [ ] OCI: frontend service (Vite build, `VITE_*` env vars at build time)
- [ ] Supabase: re-enable email confirmation for production if disabled during dev
- [ ] Run `alembic upgrade head` against production Supabase (direct connection)
- [ ] Run ingestion against production database
- [ ] End-to-end test on deployed URLs with a real Driftwood-style email account

---



## Quick reference


| Doc                                                  | Purpose                                       |
| ---------------------------------------------------- | --------------------------------------------- |
| [client-brief.md](client-brief.md)                   | What Driftwood needs and example questions    |
| [architecture.md](architecture.md)                   | System design, data model, streaming contract |
| [guides/supabase-setup.md](guides/supabase-setup.md) | Hosted Postgres + Auth                        |
| [guides/backend-setup.md](guides/backend-setup.md)   | FastAPI + Alembic commands                    |
| [guides/frontend-setup.md](guides/frontend-setup.md) | Vite + React scaffold commands                |