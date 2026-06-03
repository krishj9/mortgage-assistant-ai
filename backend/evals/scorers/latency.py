from __future__ import annotations

from typing import Iterable


def p95(values_ms: Iterable[int]) -> float:
    sorted_vals = sorted(values_ms)
    if not sorted_vals:
        return 0.0
    idx = int(0.95 * (len(sorted_vals) - 1))
    return float(sorted_vals[idx])


def score_latency(values_ms: list[int], budget_ms: float) -> dict[str, float | bool]:
    p95_val = p95(values_ms)
    return {
        "p95_ms": p95_val,
        "budget_ms": budget_ms,
        "passed": p95_val <= budget_ms,
    }
