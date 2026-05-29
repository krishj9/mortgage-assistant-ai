# MVP Phases — Completion Summary

Project: **Mortgage Loan Officer & Borrower Copilot** (Phase-1 MVP)  
Source: consolidated from `docs/phase-1-completed.md` through `docs/phase-5-completed.md`  
Last consolidated: 2026-05-29

This document replaces the individual per-phase completion files. It captures what was built across all five implementation phases from `docs/implementation-plan.md`.

---

## Overview

| Phase | Focus | Date completed |
|-------|--------|----------------|
| 1 | Workspace, core data models, auth, deal CRUD | 2026-05-26 |
| 2 | Borrower chat & Intake Agent (LangGraph + Bedrock) | 2026-05-26 |
| 3 | Document upload, Textract pipeline, extraction review API | 2026-05-27 |
| 4 | Eligibility, conditions, explanation & messaging agents | 2026-05-27 |
| 5 | LO/Processor console UI | 2026-05-27 |

**End state:** A working MVP with borrower intake chat, document upload/OCR, eligibility and messaging agents (staff APIs), and a staff console for deal review, extraction correction, eligibility override, and message approval.

---

## Phase 1 — Workspace, core data models, auth, deal CRUD

### Goals delivered

- FastAPI backend skeleton with PostgreSQL
- Core ORM schema, Alembic migrations, Pydantic contracts
- Staff and borrower authentication
- Deal CRUD APIs and synthetic seed data
- Initial Next.js frontend shell

### Key deliverables

**Backend scaffold**

- `backend/app/` — API, core, db, models, schemas, services
- `backend/alembic/` — baseline migration `0001_init.py` (`users`, `borrowers`, `deals`, `loan_applications`, `deal_contexts`, `messages`)
- Stubs for later phases: `Document`, `DocumentExtraction`, `ChatTurn`

**Core models**

- `User`, `Borrower`, `Deal` + `DealStatus`, `LoanApplication`, `DealContext`, `Messages`

**APIs**

- `POST /auth/staff/login`, `POST /auth/borrower/session`
- `POST /deals`, `GET /deals`, `GET /deals/{id}`, `PATCH /deals/{id}`

**Infrastructure & tooling**

- `infra/docker-compose.yml` — Postgres + LocalStack
- `backend/scripts/seed_synthetic.py` — staff user (`lo@example.com`), 3 borrowers, initial deals
- `uv` backend deps; Next.js 14.2.35 frontend
- Root `.gitignore`

**Frontend shell**

- Landing page, borrower login, console deals placeholder
- `lib/api/client.ts`, `lib/auth.ts`

**Tests & validation**

- Unit: `test_security.py`, `test_config.py`
- Integration: `test_auth_api.py`, `test_deals_api.py`
- Ephemeral PostgreSQL per pytest session
- `uv run alembic upgrade head`, seed, `uv run pytest -q`, frontend typecheck + build — all passing

---

## Phase 2 — Borrower chat & Intake Agent

> Reconstructed for this summary; originally implemented without a standalone completion doc.

### Goals delivered

- Structured borrower conversation filling `LoanApplicationData`
- LangGraph + Bedrock Intake Agent with validated application patching
- Chat persistence and borrower portal UI

### Key deliverables

**Chat persistence**

- `ChatTurn` model + migration `0002_chat_turns.py`

**Agent stack**

- `services/bedrock/client.py` — `get_chat_model()` (`ChatBedrockConverse`)
- `agents/tracing.py` — optional LangSmith
- `agents/state.py` — `LoanCopilotState`
- `agents/tools/application_writer.py` — deep-merge patch, Pydantic validation, `REQUIRED_FIELDS` / `missing_fields`
- `agents/prompts/intake.py`, `agents/nodes/intake_agent.py`
- `agents/orchestrator.py` — single-node graph; `run_intake_turn()` sets `Deal.status = docs_pending` when complete

**APIs**

- `POST /borrower/chat/messages`, `GET /borrower/chat/history`
- `GET /borrower/application`

**Frontend**

- `/borrower/chat` — `ChatPage`, `ChatWindow`, `ChatMessage`, `ChatInput`, `StatusPanel`
- `lib/api/borrowerChat.ts`

**Tests**

- Unit: `test_application_writer.py`, `test_intake_prompt.py`
- Integration: `test_borrower_chat_api.py`

**Deferred:** document upload (Phase 3), eligibility/messaging (Phase 4), LO console (Phase 5)

---

## Phase 3 — Document upload, Textract pipeline, extraction review API

### Goals delivered

- Borrower document upload with background OCR pipeline
- Document understanding agent and staff extraction review API
- Upload UI integrated into borrower chat

### Key deliverables

**Models & migration**

- `Document`, `DocumentExtraction` + `0003_documents.py`

**Storage & OCR**

- `services/storage/` — local + S3 abstraction (`get_storage()`)
- `services/ocr/textract.py` — AWS Textract wrapper (mockable in tests)

**Pipeline**

- `agents/nodes/document_understanding_agent.py`, `workers/document_pipeline.py` (FastAPI `BackgroundTasks`)
- `services/documents_service.py` — create/list, merge into `DealContext`, human corrections

**APIs**

- `POST/GET /documents`, `GET /documents/{id}/file`
- `GET/PUT /documents/{id}/extraction` (staff)

**Frontend**

- `DocumentUploadCard.tsx` in borrower chat with status polling
- `lib/api/documents.ts`

**Scripts & fixtures**

- `scripts/load_sample_docs.py`
- `tests/fixtures/documents/`, `tests/fixtures/ocr/`

**Tests:** 16 passing (`test_extraction_mapper.py`, `test_storage_local.py`, `test_document_pipeline.py`, `test_extraction_corrections.py`)

**Fixes during completion**

- `LocalStorage.put` — sanitized key URI bug
- `tests/conftest.py` — isolated ephemeral `DATABASE_URL` (avoid dev DB schema drift)

**Deferred:** orchestrator subgraph wiring for docs (worker calls agent directly), LO extraction UI (Phase 5), eligibility (Phase 4)

---

## Phase 4 — Eligibility, conditions, explanation & messaging agents

### Goals delivered

- Deterministic DTI/LTV rules engine with optional LLM condition refinement
- Eligibility and messaging agents with staff APIs
- Human approval gates; borrower-visible approved messages

### Key deliverables

**Schemas & migration**

- `schemas/eligibility.py` — `EligibilityResult`, `Condition`, patches, message DTOs
- `DealContext.eligibility`, `DealContext.conditions` JSON columns
- `Messages` — `internal_draft`, `borrower_draft`, approval metadata
- Migration `0004_eligibility.py`

**Agents & rules**

- `agents/tools/rules.py` — DTI/LTV thresholds (43/50, 80/95), condition templates
- `agents/nodes/eligibility_agent.py`, `agents/nodes/messaging_agent.py`
- `orchestrator.run_eligibility_then_messaging()`

**Services & APIs**

- `eligibility_service.py` — run, get, patch, approve
- `messages_service.py`, `approval_service.py`
- `POST/GET/PATCH /deals/{id}/eligibility`, `POST .../approve`
- `GET/PUT /deals/{id}/messages`, `POST .../messages/approve`
- `GET /borrower/application` with `approved_borrower_message` when approved

**Tests:** 25 passing (`test_rules.py`, `test_messaging_prompt.py`, `test_eligibility_flow.py`, `test_approval_gates.py`)

**Deferred:** LO console UI and frontend eligibility/messages clients (Phase 5)

---

## Phase 5 — LO/Processor Console UI

### Goals delivered

- Staff-facing console consuming Phases 1–4 APIs
- Document review, eligibility/conditions editing, message approval
- Borrower chat surfaces LO-approved messages as system turns

### Key deliverables

**Console shell & auth**

- `console/layout.tsx` — JWT guard, logout
- `console/login/page.tsx` — demo staff login
- Separate tokens: `lo_copilot_staff_token` vs `lo_copilot_borrower_token`

**Deal list & detail**

- `console/deals/page.tsx`, `DealList.tsx` — status filter, borrower name, last updated
- Backend `GET /deals` extended with `borrower_name`, `updated_at`
- Tabbed deal detail: Overview, Documents, Eligibility, Messages
- Components: `DealHeader`, `ConsoleNav`, `StatusChip`, `ApplicationSummary`, `DocumentList`, `DocumentViewer`, `ExtractionReview`, `EligibilityPanel`, `ConditionsEditor`, `MessageApprovalPanel`

**API clients**

- `lib/api/deals.ts`, `extractions.ts`, `eligibility.ts`, `messages.ts`, `staffAuth.ts`, `borrowerApplication.ts`

**Borrower echo**

- Approved borrower message shown in chat as a **system** turn after refresh

**Tests**

- Vitest: 3 console component tests
- Manual E2E checklist: `frontend/tests/e2e/lo_review.md`
- `npm run build` and `npm run test` pass

**Deferred:** Playwright automation, LangSmith polish, deploy hardening (Phase 6)

---

## End-to-end local run

```bash
# Infrastructure
docker compose -f infra/docker-compose.yml up -d postgres

# Backend
cd backend
export DATABASE_URL='postgresql+psycopg://loanofficer:loanofficer_password@localhost:5432/loanofficer_mvp'
export BEDROCK_MODEL_ID='anthropic.claude-3-haiku-20240307-v1:0'  # or your enabled model
uv sync --extra dev
uv run alembic upgrade head
uv run python -m scripts.seed_synthetic
uv run uvicorn app.main:app --reload

# Optional: load sample documents for deal 1
DEAL_ID=1 uv run python -m scripts.load_sample_docs

# Frontend
cd ../frontend && npm install && npm run dev
```

### Typical flows

1. **Borrower:** http://localhost:3000/borrower/login → chat → complete intake → upload documents
2. **Staff:** http://localhost:3000/console/login (`lo@example.com` / `password`) → open deal → review documents, run eligibility, edit/approve messages
3. **Borrower (after LO approval):** refresh chat to see approved LO message as system update

### Useful staff API calls

```bash
# Staff token
curl -X POST http://localhost:8000/auth/staff/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"lo@example.com","password":"password"}'

# Run eligibility
curl -X POST http://localhost:8000/deals/1/eligibility/run \
  -H "Authorization: Bearer <token>"

# Approve borrower-facing message
curl -X POST http://localhost:8000/deals/1/messages/approve \
  -H "Authorization: Bearer <token>" \
  -H 'Content-Type: application/json' \
  -d '{"channel":"borrower","approved":true}'
```

---

## Test progression by phase

| Phase | Backend tests | Frontend tests |
|-------|---------------|----------------|
| 1 | Auth, deals, security, config | typecheck + build |
| 2 | + application writer, intake prompt, borrower chat API | typecheck + build |
| 3 | 16 total | typecheck + build |
| 4 | 25 total | typecheck + build |
| 5 | (unchanged) | 3 Vitest console tests + build |

All phases validated against ephemeral PostgreSQL in pytest; frontend builds on Next.js 14 App Router.

---

## Architecture at MVP completion

```
Borrower portal                    Staff console
─────────────────                  ─────────────
/login → /chat                     /console/login → /deals
  │ Intake Agent (LangGraph)         │ Overview (application JSON)
  │ Bedrock extraction               │ Documents (preview + extraction edit)
  │ Document upload → pipeline       │ Eligibility (DTI/LTV, conditions)
  └ Approved LO message (system)     └ Message approval (internal + borrower)
         │                                    │
         └────────── PostgreSQL ──────────────┘
                    deals, loan_applications,
                    chat_turns, documents,
                    deal_contexts, messages
```

**External services:** AWS Bedrock (chat, classification fallback, messaging drafts), AWS Textract (OCR), optional LangSmith tracing, local or S3 document storage.

---

## Remaining work (post–Phase 5)

From the phase docs and implementation plan, explicitly deferred:

- **Phase 6:** Playwright E2E automation, LangSmith production polish, deployment hardening
- Orchestrator subgraph wiring for documents (worker currently calls understanding agent directly — sufficient for MVP)
- Production UI/conversational intake improvements (implemented separately after initial phase docs)

---

## Final MVP status

Phases 1–5 are **complete and validated**:

- PostgreSQL-backed core schema with Alembic migrations through `0004_eligibility` (+ later fixes such as `0005_chat_turn_role_varchar`)
- Borrower intake chat with LangGraph orchestration and Bedrock
- Document upload, Textract pipeline, and staff extraction review
- Eligibility rules engine, messaging drafts, and approval gates
- Full LO console UI and borrower portal for the demo workflow
- Passing backend pytest suite and frontend build/Vitest tests

For requirements and design intent, see `docs/requirements.md`, `docs/design.md`, and `docs/implementation-plan.md`. For system architecture, see `docs/architecture.html`.
