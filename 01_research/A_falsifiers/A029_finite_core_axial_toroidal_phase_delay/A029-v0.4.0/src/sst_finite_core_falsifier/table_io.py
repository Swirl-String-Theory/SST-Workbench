"""Canonical JSON is the hash source; Parquet is the analysis-table export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path | str, obj: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_parquet(path: Path | str, rows: list[dict[str, Any]]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path.with_suffix(path.suffix + ".json") if path.suffix else path.with_name(path.name + ".json"), rows)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return path
    table = pa.Table.from_pylist(rows or [{"_empty": True}])
    pq.write_table(table, path)
    return path


def read_parquet(path: Path | str) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()
