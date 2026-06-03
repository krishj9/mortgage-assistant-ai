from __future__ import annotations

import os

import pytest

from app.core.config import settings
from evals.scorers.messaging import score_messaging_drafts
from app.agents.nodes.messaging_agent import run_messaging_agent
from app.schemas.eligibility import ConditionsList, EligibilityResult, EligibilityStatus


pytestmark = pytest.mark.eval_smoke


def _bedrock_configured() -> bool:
    return bool(os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"))


@pytest.mark.skipif(not _bedrock_configured(), reason="AWS credentials not configured")
def test_messaging_llm_smoke():
    eligibility = EligibilityResult(status=EligibilityStatus.green, dti=0.32, ltv=0.75)
    conditions = ConditionsList(items=[])
    application = {"identity": {"borrower_name": "Alice Borrower"}, "loan_purpose": {"loan_purpose": "purchase"}}
    internal, borrower = run_messaging_agent(application, eligibility, conditions)
    scored = score_messaging_drafts(internal, borrower)
    assert scored["score"] >= 0.75, scored


@pytest.mark.skipif(not settings.LLAMA_CLOUD_API_KEY.strip(), reason="LLAMA_CLOUD_API_KEY not set")
def test_llama_cloud_key_present_for_smoke():
    assert settings.LLAMA_CLOUD_API_KEY.strip()
