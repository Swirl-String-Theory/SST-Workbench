from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    a = np.ascontiguousarray(array)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode("ascii"))
    h.update(str(a.shape).encode("ascii"))
    h.update(a.tobytes())
    return h.hexdigest()


def _json_safe(value: Any) -> Any:
    """Recursively replace non-finite numpy/Python scalars by null-safe values."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return v if np.isfinite(v) else None
    return value


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = _json_safe(payload)
    path.write_text(json.dumps(safe, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8")


def csv_dump(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def circular_distance(a: np.ndarray | float, b: np.ndarray | float, period: float = 1.0):
    d = np.asarray(a) - np.asarray(b)
    return np.abs((d + 0.5 * period) % period - 0.5 * period)


def signed_circular_delta(a: float, b: float, period: float = 1.0) -> float:
    """Return a-b wrapped to [-period/2, period/2)."""
    return float((a - b + 0.5 * period) % period - 0.5 * period)


def finite_float(value: float | np.floating) -> float:
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"non-finite scalar: {value}")
    return value
