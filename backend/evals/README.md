# Agent Evaluation (Evals) System

This directory contains datasets, scorers, and runner tools to evaluate the correctness, schemas, compliance, and latency of the LLM-based and rule-based agents (Intake, Document Understanding, Eligibility, and Messaging).

---

## 1. System Design & Components

The evaluation system is divided into four major layers:

### A. Datasets
All evaluation inputs and target (expected) ground truth outputs are defined under [datasets/](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/datasets) as JSONL files.
- `*_smoke.jsonl`: Small subset for rapid validation and CI runs.
- `*_full.jsonl`: Full test suite for thorough evaluations (e.g., nightly builds).

### B. Scorers
Heuristics and evaluation algorithms reside under `backend/evals/scorers/`:
- [schema.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/scorers/schema.py): Validates that golden example payloads conform strictly to Pydantic models.
- [intake.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/scorers/intake.py): Validates that slot-filling extraction tools successfully capture structured data (e.g., employer, email) from messages.
- [document.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/scorers/document.py): Evaluates whether document classification (W-2 vs pay stub) and extracted income maps match the expected parameters.
- [messaging.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/scorers/messaging.py): Assesses length of messaging drafts and checks compliance against a blacklist of forbidden phrases (e.g., "pre-approved", "guaranteed").
- [latency.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/scorers/latency.py): Measures performance against latency SLA targets.

### C. Test Runners
Evaluations can be run in two ways:
1. **Pytest Suite (`backend/tests/eval/`)**: Standard Pytest assertions.
   - [test_eval_schema.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/tests/eval/test_eval_schema.py): Fast schema tests.
   - [test_eval_deterministic.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/tests/eval/test_eval_deterministic.py): Heuristic and slot mapping tests.
   - [test_eval_smoke_llm.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/tests/eval/test_eval_smoke_llm.py): Bedrock LLM agent verification.
   - [test_eval_latency.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/tests/eval/test_eval_latency.py): Latency validation checks.
2. **Command Line runner [run_all.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/evals/runners/run_all.py)**: Aggregates agent execution across all datasets and outputs scores in a JSON file.

---

## 2. Environment Configuration

To run LLM-based evals, ensure your environment variables are configured correctly.

> [!IMPORTANT]
> Always execute commands from the `backend/` subdirectory so the python packages (`app`, `evals`, `scripts`) are resolved correctly.

Create or update your `backend/.env` file:
```env
# AWS Credentials for Bedrock & Textract
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Optional: Document parsing configurations
LLAMA_CLOUD_API_KEY=your_llama_cloud_key
DOCUMENT_PARSER=llamaindex

# Optional: LangSmith Observability Integration
OBSERVABILITY_PROVIDER=langsmith
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=loan-officer-copilot
```

---

## 3. Running Evaluations

Navigate to the backend directory first:
```bash
cd backend
```

### Run Local/Deterministic Evals (No LLM Calls)
These are fast, cheap, and run entirely locally without calling external LLM providers:
```bash
uv run pytest tests/eval/test_eval_schema.py tests/eval/test_eval_deterministic.py
```

### Run LLM Smoke Tests
Run evaluations that invoke the LLM (requires Bedrock credentials to be configured):
```bash
uv run pytest tests/eval -m eval_smoke
```

### Run Custom Runner Suite
Run the suite runner that gathers all stats and saves them as a JSON file:
```bash
# Smoke Suite
uv run python -m evals.runners.run_all --suite smoke --output eval-results.json

# Full Suite
uv run python -m evals.runners.run_all --suite full --output eval-results.json
```

---

## 4. LangSmith Integration

If `OBSERVABILITY_PROVIDER=langsmith` is set with a valid key, you can sync the local datasets to LangSmith:

```bash
# Sync intake datasets
uv run python -m scripts.sync_eval_datasets --dataset intake_smoke
uv run python -m scripts.sync_eval_datasets --dataset intake_full

# Sync document understanding datasets
uv run python -m scripts.sync_eval_datasets --dataset document_smoke
uv run python -m scripts.sync_eval_datasets --dataset document_full

# Sync messaging agent datasets
uv run python -m scripts.sync_eval_datasets --dataset messaging_smoke
uv run python -m scripts.sync_eval_datasets --dataset messaging_full
```
*(Implemented in [sync_eval_datasets.py](file:///Users/krishnajammula/Development/GenAI/LoanOfficer-Copilot/backend/scripts/sync_eval_datasets.py)).*

Subsequent test runs will automatically log details, tracing timelines, token usages, and inputs directly to your project page in LangSmith.
