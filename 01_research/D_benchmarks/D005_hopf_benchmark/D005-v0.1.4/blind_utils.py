from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


FORBIDDEN_BLIND_KEY_TOKENS = {
    "electron", "proton", "neutron", "alpha", "hbar", "rho_f", "fmax",
    "r_c", "rc_sst", "c_e", "ce_sst", "mass_target", "expected_hopf",
    "expected_helicity", "expected_spin", "sst_input", "sst_fields",
    "reveal_target", "particle_mapping",
}

FORBIDDEN_CANDIDATE_METADATA_KEYS = {
    "knot_type", "particle", "electron", "sst_id", "catalog_type",
    "generator_name", "physical_identity",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def canonical_json_sha256(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _walk_keys(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            key = str(k)
            yield prefix + key
            yield from _walk_keys(v, prefix + key + ".")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from _walk_keys(item, prefix + f"[{i}].")


def validate_blind_config(payload: dict) -> None:
    bad = []
    allowed_protocol_keys = {
        "protocol.sst_inputs_used",
        "protocol.target_values_allowed",
    }
    for key_path in _walk_keys(payload):
        normalized = key_path.lower()
        if normalized in allowed_protocol_keys:
            continue
        tail = normalized.split(".")[-1]
        for token in FORBIDDEN_BLIND_KEY_TOKENS:
            if token in tail:
                bad.append((key_path, token))
    if bad:
        raise ValueError(f"Blind config contains forbidden SST/target keys: {bad[:10]}")

    if payload.get("protocol", {}).get("sst_inputs_used") is not False:
        raise ValueError("blind_config.json must explicitly set protocol.sst_inputs_used=false")
    if payload.get("protocol", {}).get("target_values_allowed") is not False:
        raise ValueError("blind_config.json must explicitly set protocol.target_values_allowed=false")


def validate_candidate_npz_keys(keys: list[str]) -> None:
    lowered = {k.lower() for k in keys}
    leaking = sorted(lowered & FORBIDDEN_CANDIDATE_METADATA_KEYS)
    if leaking:
        raise ValueError(f"Candidate NPZ leaks identity metadata: {leaking}")


def assert_no_reveal_environment() -> None:
    forbidden = [k for k in os.environ if "REVEAL" in k.upper() or "SST_INPUT" in k.upper()]
    if forbidden:
        raise RuntimeError(f"Blind run refuses reveal/input environment variables: {forbidden}")


def tree_digest(root: Path, *, exclude_names: set[str] | None = None, exclude_dirs: set[str] | None = None) -> tuple[str, list[dict]]:
    exclude_names = exclude_names or set()
    exclude_dirs = exclude_dirs or set()
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        if path.name in exclude_names:
            continue
        records.append({
            "path": str(rel).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return canonical_json_sha256(records), records


def code_digest(project_root: Path) -> tuple[str, list[dict]]:
    include = []
    for pattern in ("*.py", "*.cmd", "cpp/*.cpp", "sst_hopf_native/*.py"):
        include.extend(project_root.glob(pattern))
    records = []
    for path in sorted(set(p.resolve() for p in include if p.is_file())):
        rel = path.relative_to(project_root.resolve())
        records.append({
            "path": str(rel).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    return canonical_json_sha256(records), records
