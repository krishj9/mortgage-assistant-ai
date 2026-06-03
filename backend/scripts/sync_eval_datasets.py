#!/usr/bin/env python3
"""Upload eval JSONL datasets to LangSmith (when OBSERVABILITY_PROVIDER=langsmith)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from evals import datasets_dir, load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Dataset base name, e.g. intake_smoke")
    args = parser.parse_args()

    api_key = os.environ.get("LANGSMITH_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("LANGSMITH_API_KEY is required")

    from langsmith import Client

    client = Client()
    path = datasets_dir() / f"{args.dataset}.jsonl"
    examples = list(load_jsonl(path))
    dataset_name = f"loan-copilot-{args.dataset}"
    dataset = client.create_dataset(dataset_name=dataset_name)
    for ex in examples:
        client.create_example(
            inputs=ex.get("input", {}),
            outputs=ex.get("expected", {}),
            dataset_id=dataset.id,
            metadata={"case_id": ex.get("id")},
        )
    print(f"Synced {len(examples)} examples to LangSmith dataset {dataset_name}")


if __name__ == "__main__":
    main()
