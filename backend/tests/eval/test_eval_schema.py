from __future__ import annotations

from evals.scorers.schema import validate_agent_io_examples


def test_agent_io_golden_examples_validate():
    results = validate_agent_io_examples()
    assert all(ok for _, ok, _ in results), results
