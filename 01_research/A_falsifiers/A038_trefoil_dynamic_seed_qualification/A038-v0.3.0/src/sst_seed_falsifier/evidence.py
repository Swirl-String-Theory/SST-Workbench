from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np


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
        "mesh_max_relative_rms": float(cfg.get("mesh_max_relative_rms", 1.25)),
        "hard_ds_cv": float(cfg.get("long_hard_ds_cv", 0.45)),
        "min_gap_over_ds": float(cfg.get("min_gap_over_ds", 0.9)),
        "contact_skip": int(cfg.get("contact_skip", 3)),
        "max_steps": int(cfg.get("max_steps", 300000)),
        "long_samples": int(cfg.get("long_samples", 240)),
        "replay_policy": "freeze_S40_dt_and_guard_stride_for_base_and_perturbations",
        "require_native": bool(cfg.get("require_native", True)),
    }
    return contract, object_sha256(contract)


def code_manifest(package_root):
    package_root = Path(package_root)
    code_files = []
    for rel in ("src", "cpp", "tests"):
        path = package_root / rel
        if path.exists():
            for row in tree_manifest(path, {".py", ".cpp", ".h", ".md", ".toml", ".json", ".cmd", ".yaml", ".yml", ".pyd", ".so"}):
                row["path"] = f"{rel}/{row['path']}"
                code_files.append(row)
    return code_files


def build_evidence_manifest(package_root, dataset, config_path, cfg):
    dataset = Path(dataset)
    code_files = code_manifest(package_root)
    dataset_files = tree_manifest(dataset, set(cfg.get("extensions", [".txt", ".xyz", ".dat"])) | {".json"}) if dataset.exists() else []
    thresholds = {k: v for k, v in cfg.items() if any(token in k for token in ("threshold", "_max", "_min", "_tol", "_floor", "_band", "margin"))}
    return {
        "format": FORMAT,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "run_kind": str(cfg.get("run_kind", "blind_scientific")),
        "package_version": __import__("sst_seed_falsifier",fromlist=["__version__"]).__version__,
        "release_identity": __import__("sst_seed_falsifier.release",fromlist=["release_identity"]).release_identity(),
        "runtime": {"python": sys.version, "numpy": np.__version__, "platform": platform.platform()},
        "config_path": str(config_path) if config_path is not None else None,
        "config_sha256": file_sha256(config_path) if config_path is not None else object_sha256(cfg),
        "configuration": cfg,
        "thresholds": thresholds,
        "config_object_sha256": object_sha256(cfg),
        "thresholds_sha256": object_sha256(thresholds),
        "code_manifest_sha256": object_sha256(code_files),
        "code_files": code_files,
        "dataset_root": str(dataset),
        "dataset_manifest_sha256": object_sha256(dataset_files),
        "dataset_files": dataset_files,
        "physics_scope": "regularized filament / finite-core surrogate only",
        "knot_library_dependency": (__import__("sst_seed_falsifier.knot_library",fromlist=["current_attestation"]).current_attestation()
                                    if cfg.get("require_knot_library_records",False) else None),
    }


def archive_evidence(package_root, dataset, config_path, cfg, out, private):
    from .io import dump_json
    full = build_evidence_manifest(package_root, dataset, config_path, cfg)
    dump_json(Path(private) / "EVIDENCE_MANIFEST_PRIVATE.json", full)
    public = {k: v for k, v in full.items() if k not in {
        "dataset_root", "dataset_files", "config_path", "configuration"
    }}
    public["dataset_file_count"] = len(full["dataset_files"])
    public["private_evidence_sha256"] = object_sha256(full)
    public["source_identities_hidden"] = True
    dump_json(Path(out) / "EVIDENCE_MANIFEST.json", public)
    return public


def validate_frozen_evidence(out, cfg, config_path=None):
    """Scoring reads only public commitments, never the sealed source identities."""
    from .io import load_json
    frozen = load_json(Path(out) / "EVIDENCE_MANIFEST.json")
    if frozen["config_object_sha256"] != object_sha256(cfg):
        raise ValueError("FROZEN_CONFIG_MISMATCH")
    if config_path is not None and frozen["config_sha256"] != file_sha256(config_path):
        raise ValueError("FROZEN_CONFIG_FILE_MISMATCH")
    from .release import release_identity
    rel=release_identity()
    if not rel.get("match") or frozen.get("release_identity",{}).get("release_sha256")!=rel.get("release_sha256"):
        raise ValueError("FROZEN_RELEASE_IDENTITY_MISMATCH")
    current = code_manifest(Path(__file__).resolve().parents[2])
    if frozen["code_manifest_sha256"] != object_sha256(current):
        raise ValueError("FROZEN_CODE_MISMATCH")
    if cfg.get("require_knot_library_records",False):
        from .knot_library import current_attestation
        if current_attestation() != frozen.get("knot_library_dependency"):
            raise ValueError("FROZEN_KNOT_LIBRARY_DEPENDENCY_MISMATCH")
    prepare = load_json(Path(out) / "prepare_summary.json")
    if cfg.get("run_kind", "blind_scientific") == "blind_scientific" and prepare.get("source_diversity_status") != "PASS_SOURCE_DIVERSITY":
        raise ValueError(prepare.get("source_diversity_status", "SOURCE_DIVERSITY_UNVERIFIED"))
