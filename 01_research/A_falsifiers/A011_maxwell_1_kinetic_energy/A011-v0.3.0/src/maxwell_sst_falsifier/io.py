from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ffloat(row: dict[str, str], key: str, default: float | None = None) -> float | None:
    value = row.get(key, "")
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def fint(row: dict[str, str], key: str, default: int = 0) -> int:
    value = row.get(key, "")
    if value is None or str(value).strip() == "":
        return default
    return int(float(value))


def fbool(row: dict[str, str], key: str, default: bool = False) -> bool:
    value = row.get(key, "")
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
