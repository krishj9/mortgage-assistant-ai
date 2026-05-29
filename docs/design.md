Document ID: DES‑LOAN‑COPILOT‑MVP‑001
Version: 1.0
Status: Draft
Project: Mortgage Loan Officer & Borrower Copilot – MVP
Last Updated: 2026‑05‑26
Owner: Engineering

1. Architecture overview
The system is a web application with a React front end, a FastAPI backend, and a LangGraph‑based agent orchestration layer that calls AWS Bedrock LLMs and a managed OCR/IDP service.

The backend maintains per‑deal state (loan_application, deal_context, approvals) in a database and object storage for documents; LangSmith captures traces for all agent runs.

At a high level:

Frontend:

Borrower Portal: chat intake + document upload.

LO Console: deal list, intake summary, documents, extraction review, eligibility & conditions, message approval.

Backend APIs (FastAPI):

Auth, session, and user management.

Borrower chat events, application data API.

Document upload and retrieval API.

Agent orchestration endpoints (start/continue flows).

Agent Layer (LangGraph + Bedrock):

Borrower Chat & Intake Agent.

Document Understanding Agent.

Eligibility & Conditions Agent.

Explanation & Messaging Agent.

Orchestrator node that manages state transitions.

Services:

OCR/IDP (e.g., Azure Document Intelligence / AWS Textract).

Data store (e.g., DynamoDB or relational DB) for deals and structured fields.

Object storage (e.g., S3) for documents and derived artifacts.

2. Component breakdown
2.1 Frontend – Borrower Portal (React)
Chat UI component:

Renders conversational turns from the backend.

Sends user messages and structured answers to FastAPI endpoints.

Displays inline steps (e.g., “Now upload your pay stub”) and progress.

Document upload component:

Accepts PDF/images, shows upload status, and surfaces extracted summaries when available.

Status summary panel:

High‑level view of what has been captured (income, assets, property) and uploaded docs.

2.2 Frontend – LO/Processor Console (React)
Deal list & filters:

Displays deals by status (intake in progress, docs pending, ready for review, completed).

Deal detail view:

Application summary (as captured by chat).

Document list with type, extraction status, and links to view.

Extraction review panels:

For income, assets, and metadata, show extracted fields alongside a document viewer.

Eligibility & conditions panel:

Shows computed DTI/LTV, suggested status, and conditions list.

Contains controls to override/approve.

Message approval panel:

Shows internal rationale and borrower‑facing text.

Provides WYSIWYG or text editor and “approve” toggle.

2.3 Backend – FastAPI
API modules:

auth: borrower and staff authentication and session handling.

borrower_chat: endpoints to send/receive chat messages, orchestrate Intake Agent.

documents: upload, list, retrieval, and trigger to call Document Understanding Agent.

deals: CRUD for Deal and DealContext entities.

eligibility: endpoint to trigger Eligibility & Conditions Agent, store outputs.

messages: fetch and update internal and borrower‑facing messages, mark approvals.

Responsibilities:

Enforce access control and scoping.

Persist application and extracted data.

Coordinate between HTTP world and LangGraph workflows.

2.4 Agent layer – LangGraph + Bedrock
Graph nodes:

Borrower Chat & Intake Agent

Input: latest borrower message, current loan_application partial.

Tools:

Schema validation helper (Python tool) to update loan_application.

Behavior:

Interprets borrower message.

Asks follow‑up questions to complete required fields.

Invokes a “prompted tool” to push structured updates to the backend.

Document Understanding Agent

Input: document metadata (path, MIME type), doc type prediction (optional), deal ID.

Tools:

Document classifier model or endpoint for mortgage docs.

OCR/IDP API client.

Mapping functions (Python tools) that convert OCR outputs into normalized income/assets/application entities.

Behavior:

Classifies document.

Runs OCR/IDP.

Maps structured fields into deal_context.

Writes extraction results and confidence scores to DB.

Eligibility & Conditions Agent

Input: loan_application, deal_context (including human‑corrected fields if available).

Tools:

Rule evaluation module (Python) encapsulating DTI/LTV thresholds.

Behavior:

Computes DTI/LTV.

Assigns status (green/yellow/red).

Generates a structured conditions list (machine‑readable).

Explanation & Messaging Agent

Input: loan_application, deal_context, eligibility result, conditions list.

Behavior:

Generates internal rationale and borrower‑facing message using Bedrock LLMs.

Grounded on structured fields and rule results, not raw free‑text, to keep responses stable.

Orchestrator

Implemented as the LangGraph controller plus a thin backend workflow layer.

Responsibilities:

When intake completes, ensure required minimal data is present.

When docs upload completes, schedule Document Understanding Agent for each file.

After extraction and human review, trigger Eligibility & Conditions Agent.

After eligibility, trigger Explanation & Messaging Agent and mark deal “ready for LO approval.”

2.5 Data storage
Relational or DynamoDB tables (simplified logical model):

Borrower (id, name, contact info).

Deal (id, borrower_id, status, timestamps).

LoanApplication (deal_id, structured application fields; 1:1 with deal).

DealContext (deal_id, extracted income/assets/liabilities, computed metrics, status flags).

Document (id, deal_id, storage_uri, predicted_type, extraction_status).

DocumentExtraction (document_id, extracted JSON, confidence, human_corrections).

Messages (deal_id, internal_notes, borrower_message, approval_flags).

Object storage:

Raw documents and optionally HTML/PDF renditions used in the viewer.

3. External integrations
LLM provider – AWS Bedrock

Used for all conversational logic (borrower chat, explanations, some classification fallbacks).

Wrapped in LangGraph with safety and guardrail prompts.

OCR/IDP service

Azure Document Intelligence / AWS Textract / Google Document AI selected for their mortgage/document models and table extraction capabilities.

Called via backend client; results mapped into internal schemas.

Observability – LangSmith and logging

All agent runs registered in LangSmith projects with tags (borrower_chat, doc_understanding, eligibility, messaging).

Backend logs correlated with LangSmith trace IDs for debugging.

4. Agent prompt and context strategy (high level)
Borrower Chat & Intake Agent

System prompt: “You are a mortgage intake assistant helping borrowers fill out a simplified loan application. Ask only one clarifying question at a time, and map answers to specific fields.”

Context:

Current loan_application snapshot.

Short summary of previous turns, not full history.

Document Understanding Agent

System prompt: “You interpret OCR output from mortgage documents and map them into a fixed JSON schema for income, assets, and applicant metadata. Do not guess values that are not clearly present.”

Context:

OCR raw text and key‑value pairs.

Any prior extractions for this deal (for cross‑validation).

Eligibility & Conditions Agent

System prompt: “You are an assistant applying a simple set of rules to decide if a borrower is likely pre‑qualified. You must rely only on structured fields and explicit rule thresholds.”

Context:

Structured application and deal context.

Rules summary (DTI/LTV thresholds, basic requirements).

Explanation & Messaging Agent

System prompt: “You explain mortgage pre‑qualification status to internal staff and borrowers in clear, honest language. You do not make binding commitments or legal claims.”

Context:

Eligibility result and conditions list.

Borrower’s main goals (e.g., purchase vs refi, timing).

5. Security and compliance considerations (MVP‑level)
Use synthetic data only; all PII fields in test environments are synthetic values.

Ensure strong separation of borrower and staff surfaces; borrowers can only see their own application and messages, not internal notes.

Clearly label all borrower‑facing outputs as informational drafts subject to LO review, avoiding terms like “final approval.”

6. Phasing and extensibility hooks
Phase‑1 focuses on:

W‑2 borrowers.

Limited document types.

Simplified eligibility rules.

Extensibility points:

Add more doc types and specialized extraction pipelines.

Introduce vector‑database‑backed RAG over real guidelines and FAQs.

Integrate with LOS and pricing engines for more realistic workflows.