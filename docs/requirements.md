Document ID: REQ‑LOAN‑COPILOT‑MVP‑001
Version: 1.0
Status: Draft
Project: Mortgage Loan Officer & Borrower Copilot – MVP (Doc AI + Borrower Chat)
Last Updated: 2026‑05‑26
Owner: Product / Engineering

1. Overview
Build a mortgage copilot that helps loan officers (LOs) and processors pre‑qualify borrowers by combining borrower‑facing chat intake, document understanding, and agentic reasoning with strict human‑in‑the‑loop control.

The MVP focuses on a narrow, realistic slice: W‑2 style borrowers, a small set of common documents, and synthetic data/documents only.

2. Goals and non‑goals
2.1 Goals
Enable borrowers to submit a simplified mortgage application and upload key documents via a conversational web UI.

Automatically classify and OCR a small set of uploaded mortgage documents and extract structured income and asset data.

Generate a draft pre‑qualification assessment and conditions list for an LO/processor to review and approve.

Provide clear, editable borrower‑facing explanations and document requests, always gated by human approval.

Demonstrate a multi‑agent architecture (intake, document understanding, eligibility, explanation, orchestrator) with observable traces.

2.2 Non‑goals (Phase‑1)
No real credit pulls, pricing engine integration, or binding credit decisions.

No complex product libraries or investor‑specific guideline matrices (conventional vs FHA/VA/USDA etc.).

No support for self‑employed, non‑traditional income, or multiple borrowers beyond simple, synthetic examples.

No production integrations with an LOS; Phase‑1 stops at internal “reviewed pre‑qual notes” in the copilot UI.

3. Personas and user stories
3.1 Borrower
As a borrower, I want to chat with a guided assistant that asks me questions in plain language and fills the application for me, so I do not have to interpret long forms.

As a borrower, I want to know exactly what documents are needed and why, so I understand the process and feel less anxious.

As a borrower, I want to upload my documents directly in the portal during the chat, rather than emailing attachments.

3.2 Loan officer / processor
As a loan officer, I want a summarized view of the borrower’s application, extracted income and asset data, and suggested conditions, so I can quickly decide if the borrower appears pre‑qualified.

As a processor, I want to see each document’s extracted fields side‑by‑side with the original, so I can correct errors before they affect decisions.

As a loan officer, I want the system to draft borrower‑facing explanations and requests that I can edit, so I save time but remain in full control.

4. Scope
4.1 In‑scope features (Phase‑1 MVP)
Borrower‑facing web chat UI:

Conversational intake that captures a simplified 1003‑like application: identity, contact, employment, income, assets, liabilities, property, loan purpose.

Inline document upload prompts (e.g., “Please upload your most recent pay stub”).

Document understanding:

Multi‑document classification for a small set of types:

Pay stub.

W‑2 (or equivalent annual income summary).

Bank statement.

Application/1003‑like PDF (optional, can be synthetic).

OCR using a managed service (e.g., Textract, Azure Document Intelligence, Google Document AI).

Table and key‑value extraction to produce normalized structured entities:

Income records (gross income, pay frequency, employer).

Asset records (account type, average balance, recent large deposits).

Applicant metadata (name, address, SSN placeholder tokens, employer, etc.).

Agentic reasoning and workflow:

Intake Agent that normalizes chat answers into a loan_application object.

Document Understanding Agent that classifies docs, calls OCR/IDP, and maps extracted data into deal_context.

Eligibility & Conditions Agent that:

Computes approximate DTI/LTV using loan_application + extracted_data.

Assigns a simple status: green (likely pre‑qualifiable), yellow (borderline / needs more data), red (unlikely).

Suggests 1–5 conditions (e.g., “Need second pay stub”, “Clarify large deposit on 04/15”).

Explanation & Messaging Agent that drafts:

Internal rationale for LO/processor.

Borrower‑facing message summarizing status and next steps.

Human‑in‑the‑loop:

LO/processor must approve or edit the eligibility status, conditions list, and any borrower‑facing messages before they are persisted as “final” or shown to the borrower.

Processor must review and can correct extracted fields for each document; corrections are saved back into deal_context.

Data and environment:

Synthetic borrowers and documents only; no real PII or production connections.

Backend APIs using FastAPI, frontend using React, and agent orchestration using LangGraph with AWS Bedrock as the primary LLM provider.

Basic observability: request/response logging and LangSmith traces for agent runs.

4.2 Out of scope (Phase‑1)
Pricing, product eligibility engines, and live rate quotes.

Full set of mortgage document types (e.g., tax returns, VOE, VOI, HOA docs).

Mobile native apps; MVP is browser‑based, responsive web only.

Multi‑borrower, multi‑property, and complex ownership structures.

5. Functional requirements
5.1 Borrower chat intake
The system shall provide a secure borrower web page with a chat‑like interface.

The chat shall collect the following minimum fields:

Borrower name, DOB placeholder, contact info.

Employment status (employed, self‑employed, retired; Phase‑1 focuses on employed).

Income amount and frequency.

Assets (accounts with balances).

Basic liabilities (monthly non‑housing debt payments).

Property status (under contract, shopping, refinance) and estimated value or purchase price.

Desired down payment or cash available.

The chat shall validate numeric fields and prompt for missing information before marking intake complete.

5.2 Document upload and management
The borrower chat UI shall allow upload of up to N documents per session (configurable).

Uploaded documents shall be stored in an internal storage bucket with metadata (borrower ID, doc type prediction, upload timestamp).

The system shall display each uploaded document in the LO/processor console with its predicted type and extraction status.

5.3 Document understanding
For each uploaded PDF/image, the system shall:

Predict document type among the supported set.

Run OCR/IDP to extract text and structured data (tables, key‑value pairs).

Map extracted fields into normalized internal entities (income, assets, metadata), filling a deal_context record.

The LO/processor console shall present extracted fields side‑by‑side with the original document for verification and allow edits.

Edits made by a human reviewer shall overwrite or augment the machine‑extracted values in deal_context.

5.4 Eligibility & conditions
The system shall compute approximate:

DTI = (sum of monthly debts + estimated housing payment) / estimated monthly income.

LTV = loan amount / property value.

The system shall apply a simple, configurable ruleset to assign:

green if DTI and LTV are below configured thresholds and required fields are present.

yellow if near thresholds or some key data is missing.

red if clearly outside thresholds or critical data is missing.

The system shall generate a draft conditions list based on missing data and simple patterns (e.g., recent large deposits, single pay stub only).

5.5 Explanation & messaging
The system shall generate internal LO/processor notes explaining:

Why the borrower appears green/yellow/red.

What conditions are recommended and why.

The system shall generate a borrower‑facing message that:

Summarizes their status in plain language.

Lists documents still needed and what they prove (e.g., “Pay stubs help us confirm your income”).

The LO/processor must approve or edit both internal and external messages before they can be saved as final or shown in the borrower chat.

5.6 Review and approval workflow
The LO/processor console shall show a checklist view:

Application intake completeness.

Document upload and extraction status.

Conditions list and approval flag.

Borrower‑facing message and approval flag.

The system shall not display any pre‑qual status or conditions to the borrower until all required human approvals are recorded.

6. Non‑functional requirements
Security:

All endpoints must be authenticated for LO/processor access; borrower sessions must be scoped to their own application only.

All data in transit must use HTTPS; data at rest must be encrypted.

Performance:

Single document classification + OCR + mapping should typically complete within 5–10 seconds per document in the MVP environment.

Observability:

All agent runs shall be traced in LangSmith with metadata linking them to the borrower/deal ID.

Key events (intake complete, document extracted, eligibility computed, messages approved) shall be logged with timestamps.

Deployability:

The system shall be deployable to a single cloud environment (e.g., AWS) using infrastructure as code (Terraform) and CI/CD (GitHub Actions) in later phases.

7. Risks and open questions
Accuracy of OCR/IDP for synthetic documents may not reflect production quality; need scenarios that stress extraction edge cases.

Regulatory positioning (what is “pre‑qualification” vs “pre‑approval”) is out of scope; messaging must clearly state outputs are drafts for LO review.

Future phases may require more sophisticated guideline logic and RAG over real policy documents, which will affect data models and prompts.

High‑level design document (design.md)

