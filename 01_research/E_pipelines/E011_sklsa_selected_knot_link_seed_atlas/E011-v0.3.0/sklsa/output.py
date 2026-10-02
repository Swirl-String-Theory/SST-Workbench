from __future__ import annotations
from pathlib import Path
import csv
import json


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fields:
        path.write_text("", encoding="utf-8")
        return
    if fields is None:
        fields = []
        seen = set()
        for row in rows:
            for k in row:
                if k not in seen and not isinstance(row[k], (dict, list)):
                    seen.add(k); fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            flat = {k: (json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v) for k, v in row.items()}
            w.writerow(flat)
