from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_benchmark(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_benchmark_files(directory: str | Path, pattern: str = "*.json") -> list[Path]:
    return sorted(Path(directory).glob(pattern))


def save_benchmark(payload: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
