from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def load_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def datasets_dir() -> Path:
    return Path(__file__).resolve().parent / "datasets"
