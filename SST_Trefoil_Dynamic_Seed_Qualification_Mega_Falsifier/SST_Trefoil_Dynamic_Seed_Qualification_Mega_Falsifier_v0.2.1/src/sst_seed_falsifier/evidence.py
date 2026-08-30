from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


FORMAT = "SST-TREFOIL-EVIDENCE-1"


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def object_sha256(obj):
    return hashlib.sha256(_canonical(obj)).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_manifest(root, include_suffixes=None):
    root = Path(root)
    suffixes = None if include_suffixes is None else {s.lower() for s in include_suffixes}
    rows = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.as_posix().lower()):
        if any(part in {"__pycache__", ".pytest_cache", ".venv", "build"} for part in path.parts):
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        rows.append({"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path), "bytes": path.stat().st_size})
    return rows


def dynamics_contract(cfg, resolution):
    """Frozen discretized orbital map shared by S40 and S50.

    The integration horizon is intentionally absent: S40 searches it and S50 replays
    the same map at the selected return time.
    """
    contract = {
        "format": "SST-TREFOIL-DYNAMICS-CONTRACT-1",
        "physical_model": "regularized_vortex_filament_surrogate",
        "core_mode": "global_volume",
        "gamma": float(cfg.get("gamma", 1.0)),
        "core_fraction": float(cfg["core_fraction"]),
        "resolution": int(resolution),
        "integrator": "RK4",
        "dt_policy": "dt_factor_times_min_ds_squared_over_abs_gamma",
        "dt_factor": float(cfg.get("dt_factor", 0.025)),
        "mesh_enabled": True,
        "mesh_method": str(cfg.get("mesh_redistribution_method", "segment_feedback")),
        "mesh_rate": float(cfg.get("mesh_rate", 4.0)),
        "mesh_max_relative_rms": float(cfg.get("mesh_max_relative_rms", 1.0)),
        "hard_ds_cv": float(cfg.get("long_hard_ds_cv", 0.45)),
        "min_gap_over_ds": float(cfg.get("min_gap_over_ds", 0.85)),
        "require_native": bool(cfg.get("require_native", True)),
    }
    return contract, object_sha256(contract)


def build_evidence_manifest(package_root, dataset, config_path, cfg):
    package_root = Path(package_root)
    dataset = Path(dataset)
    config_path = Path(config_path)
    code_files = []
    for rel in ("src", "cpp", "tests"):
        path = package_root / rel
        if path.exists():
            for row in tree_manifest(path, {".py", ".cpp", ".h", ".md", ".toml", ".json", ".cmd", ".yaml", ".yml"}):
                row["path"] = f"{rel}/{row['path']}"
                code_files.append(row)
    dataset_files = tree_manifest(dataset, cfg.get("extensions", [".txt", ".xyz", ".dat"])) if dataset.exists() else []
    thresholds = {k: v for k, v in cfg.items() if any(token in k for token in ("threshold", "_max", "_min", "_tol", "_floor", "_band", "margin"))}
    return {
        "format": FORMAT,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": str(cfg.get("run_kind", "blind_scientific")),
        "package_version": "0.2.1",
        "config_path": str(config_path),
        "config_sha256": file_sha256(config_path),
        "config_object_sha256": object_sha256(cfg),
        "thresholds_sha256": object_sha256(thresholds),
        "code_manifest_sha256": object_sha256(code_files),
        "code_files": code_files,
        "dataset_root": str(dataset),
        "dataset_manifest_sha256": object_sha256(dataset_files),
        "dataset_files": dataset_files,
        "physics_scope": "regularized filament / finite-core surrogate only",
    }
