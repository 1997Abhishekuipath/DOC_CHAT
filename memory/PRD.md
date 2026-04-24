# DocChat — Enterprise RAG Platform (PRD)

## Original Problem Statement
Build DocChat — an enterprise-grade, production-ready RAG platform that lets users upload documents and have AI-powered conversations grounded strictly in those documents, with citations, access control, and secure sharing. 10 phases, 18 feature flags, 4 roles. Preserve and extend existing functionality.

## User Choices (from ask_human)
- LLM Provider: **OpenRouter** (user has own API key)
- Embeddings: **OpenAI text-embedding-3-small** (user has own API key)
- OCR: **Tesseract** (deferred to later phase)
- Implementation Priority: All phases sequentially
- Database scope: Use **MongoDB** for MVP (PostgreSQL deferred — user explicitly approved)
- API keys: user will add later

## Architecture Decisions (MVP)
- Backend: FastAPI (async) + MongoDB (motor) + ChromaDB (local persistent)
- Frontend: React + shadcn/UI + Cabinet Grotesk / IBM Plex Sans + Phosphor icons + Recharts
- RAG: OpenRouter (OpenAI-compatible SDK) + OpenAI embeddings + ChromaDB vector store
- Streaming: FastAPI StreamingResponse with SSE-style `event:`/`data:` format
- Background jobs: FastAPI BackgroundTasks (Celery/Redis deferred)
- Auth: JWT access+refresh tokens, bcrypt password hashing, RBAC via dependency
- Share links: random opaque tokens + server-side scope enforcement + short-lived guest JWT

## User Personas
1. **Owner** — admin, full workspace control, analytics access, user management
2. **Editor** — uploads/manages own documents, creates share links
3. **Viewer** — reads granted documents, chats within scope
4. **Public Guest** — accesses only share-token-scoped documents, strictly read-only

## What's Been Implemented (2026-04-24)
### Backend
- JWT auth: register / login / refresh / me
- RBAC dependency (`require_role`) enforced on every protected route
- Document upload (PDF / DOCX / TXT / MD) with text extraction (pypdf, python-docx)
- Tiktoken chunking (cl100k_base, 500 tokens, 75 overlap)
- OpenAI text-embedding-3-small → ChromaDB (cosine)
- Background ingestion with real-time progress status
- RAG retrieval + OpenRouter streaming chat
- Inline citations with page numbers
- Confidence scoring from retrieval distance (HIGH / MEDIUM / LOW)
- Follow-up question suggestions
- Conversation sessions (persistent, rename, delete)
- Thumbs up/down feedback
- Share links: public / password / expiring / single-use / domain restriction / revoke
- Guest chat endpoint scoped via JWT containing document_ids (enforced in Chroma WHERE clause)
- Admin analytics (totals, latency percentiles, feedback, daily series, confidence dist)
- Admin audit log
- Admin user management (change role)
- Feature flags endpoint

### Frontend
- Landing page (Swiss high-contrast, cobalt primary, structural imagery)
- Login / Register (split-screen layout, Cabinet Grotesk)
- App Layout (sidebar with workspace/admin/account sections)
- Documents Dashboard (table list, status badges, progress bars, tags, bulk chat)
- Upload Dialog (drag-drop style, tags)
- Chat (streaming SSE, citation badges, confidence badges, source previews, follow-ups, feedback, copy, markdown)
- Share Links Manager (create dialog with full options, copy URL, revoke)
- Public Guest Share view (gate flow for password/domain, scoped chat)
- Admin Analytics (Recharts line + bar, stat cards)
- Admin Audit Log (filterable table)
- Admin Users (inline role edit)
- Settings (profile + feature flag viewer)

## Deferred (Prioritized Backlog)
### P0 (blocking for full spec)
- User must add OPENROUTER_API_KEY and OPENAI_API_KEY to /app/backend/.env
- Document preview panel with passage highlighting (currently only shows excerpt in dialog)
- Per-document ACL grants (currently only owner/creator access)

### P1 (post-MVP enhancements)
- Hybrid BM25 + vector search with toggle
- Query rewriting + multi-query expansion
- Cross-encoder reranking
- OCR (Tesseract) for scanned PDFs
- Table extraction for XLSX/CSV
- PPTX, HTML, CSV parsers
- Entity extraction (NER)
- PII masking on ingestion
- Retention policies + scheduled cleanup
- Secondary LLM hallucination verification
- Conflict detection between sources
- Embedding cache + query result cache (Redis)
- Incremental indexing on document update
- Celery worker for ingestion (currently FastAPI BackgroundTasks)
- PostgreSQL migration + Alembic (currently MongoDB)
- Multi-hop reasoning
- Hierarchical retrieval
- Personalized retrieval

### P2 (infrastructure)
- docker-compose.yml with postgres/redis/celery services
- Rate limiting (Redis-backed)
- Structured request logging middleware
- WCAG 2.1 AA audit pass
- Load testing scripts

## Runtime Configuration
- Env vars: MONGO_URL, DB_NAME, JWT_SECRET, SHARE_TOKEN_SECRET, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENAI_API_KEY, EMBEDDING_MODEL, UPLOAD_DIR, CHROMA_DIR
- Feature flags (all ENV driven): listed in core/config.py

## Next Actions
1. User adds OPENROUTER_API_KEY and OPENAI_API_KEY
2. User registers first account (auto-becomes Owner)
3. User uploads test PDF/DOCX and verifies chat flow
4. Future: phase 2 (hybrid search + reranking)
