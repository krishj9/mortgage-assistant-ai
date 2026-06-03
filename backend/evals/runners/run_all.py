from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals import datasets_dir, load_jsonl
from evals.scorers.document import score_document_case
from evals.scorers.intake import score_intake_l0_case
from evals.scorers.messaging import score_messaging_drafts
from evals.scorers.schema import score_schema_compliance
from app.agents.nodes.messaging_agent import _template_messages
from app.schemas.eligibility import ConditionsList, EligibilityResult, EligibilityStatus


def run_suite(suite: str) -> dict:
    suffix = "smoke" if suite == "smoke" else "full"
    results: dict = {"suite": suite, "agents": {}}

    intake_path = datasets_dir() / f"intake_{suffix}.jsonl"
    if not intake_path.exists():
        intake_path = datasets_dir() / "intake_smoke.jsonl"
    intake_scores = [score_intake_l0_case(case) for case in load_jsonl(intake_path)]
    results["agents"]["intake"] = {
        "mean_score": sum(s["score"] for s in intake_scores) / max(len(intake_scores), 1),
        "cases": intake_scores,
    }

    doc_path = datasets_dir() / f"document_{suffix}.jsonl"
    if not doc_path.exists():
        doc_path = datasets_dir() / "document_smoke.jsonl"
    doc_scores = [score_document_case(case) for case in load_jsonl(doc_path)]
    results["agents"]["document"] = {
        "mean_score": sum(s["score"] for s in doc_scores) / max(len(doc_scores), 1),
        "cases": doc_scores,
    }

    msg_path = datasets_dir() / f"messaging_{suffix}.jsonl"
    if not msg_path.exists():
        msg_path = datasets_dir() / "messaging_smoke.jsonl"
    msg_scores = []
    for case in load_jsonl(msg_path):
        status = EligibilityStatus(case["input"]["status"])
        eligibility = EligibilityResult(status=status, dti=0.35, ltv=0.8)
        conditions = ConditionsList(items=[])
        internal, borrower = _template_messages(
            eligibility, conditions, case["input"].get("borrower_name")
        )
        scored = score_messaging_drafts(internal, borrower)
        msg_scores.append({"case_id": case["id"], **scored})
    results["agents"]["messaging"] = {
        "mean_score": sum(s["score"] for s in msg_scores) / max(len(msg_scores), 1),
        "cases": msg_scores,
    }

    results["schema_compliance"] = score_schema_compliance()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval suite")
    parser.add_argument("--suite", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    results = run_suite(args.suite)
    payload = json.dumps(results, indent=2)
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
