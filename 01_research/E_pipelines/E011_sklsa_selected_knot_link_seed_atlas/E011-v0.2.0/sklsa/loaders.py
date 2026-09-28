from __future__ import annotations
from pathlib import Path
import csv
import json


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def read_source_matrix(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def qualification_paths(e010_output: Path, topology_id: str) -> dict[str, Path]:
    q = e010_output / "atlas" / topology_id / "qualification"
    return {
        "root": q,
        "gate": q / "PRODUCTION_GATE.json",
        "summary": q / "summary.json",
        "source_matrix": q / "source_matrix.csv",
        "independence": q / "source_independence_ledger.json",
        "convergence": q / "convergence.json",
        "metrics": q / "geometry_metrics.json",
        "topology_checks": q / "topology_checks.json",
    }


def load_topology_bundle(e010_output: Path, topology_id: str) -> dict:
    p = qualification_paths(e010_output, topology_id)
    required = ["gate", "summary", "source_matrix", "independence", "convergence", "metrics"]
    missing = [name for name in required if not p[name].is_file()]
    if missing:
        return {
            "topology_id": topology_id,
            "status": "MISSING_E010_QUALIFICATION_ARTIFACTS",
            "missing": missing,
            "paths": {k: str(v) for k, v in p.items()},
        }
    return {
        "topology_id": topology_id,
        "status": "LOADED",
        "gate": read_json(p["gate"]),
        "summary": read_json(p["summary"]),
        "source_matrix": read_source_matrix(p["source_matrix"]),
        "independence": read_json(p["independence"]),
        "convergence": read_json(p["convergence"]),
        "metrics": read_json(p["metrics"]),
        "topology_checks": read_json(p["topology_checks"]) if p["topology_checks"].is_file() else None,
        "paths": {k: str(v) for k, v in p.items()},
    }
