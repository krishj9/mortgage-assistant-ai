from __future__ import annotations

import pytest

from evals.scorers.latency import score_latency

pytestmark = pytest.mark.eval_latency


def test_latency_budget_helper():
    values = [100] * 18 + [5000, 5000]
    result = score_latency(values, budget_ms=1000.0)
    assert result["p95_ms"] == 5000.0
    assert result["passed"] is False
