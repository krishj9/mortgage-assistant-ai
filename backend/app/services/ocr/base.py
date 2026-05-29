from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OcrResult:
    text: str = ""
    key_values: dict[str, str] = field(default_factory=dict)
    tables: list[list[list[str]]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
