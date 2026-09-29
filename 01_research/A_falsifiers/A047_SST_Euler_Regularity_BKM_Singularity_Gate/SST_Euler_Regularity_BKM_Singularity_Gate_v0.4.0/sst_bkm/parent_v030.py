from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import zipfile

PARENT_NAME = "SST_Euler_Regularity_BKM_Singularity_Gate_v0.3.0-outputs"


def _load_json(path: Path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def locate_parent_output(arg: str | None, version_root: Path) -> Path:
    candidates = []
    if arg:
        candidates.append(Path(arg))
    env = os.environ.get("A047_V030_OUTPUT")
    if env:
        candidates.append(Path(env))
    vr = Path(version_root).resolve()
    family = vr.parent
    candidates += [
        family / "SST_Euler_Regularity_BKM_Singularity_Gate_v0.3.0" / PARENT_NAME,
        family / PARENT_NAME,
        vr / PARENT_NAME,
    ]
    for p in candidates:
        p = p.expanduser()
        if p.is_dir() and (p / "BLIND" / "summary.json").is_file():
            return p.resolve()
    raise FileNotFoundError(
        "A047-v0.3.0 output folder not found. Pass --parent-v030-output or set A047_V030_OUTPUT. "
        f"Expected a folder containing BLIND/summary.json; tried: {[str(x) for x in candidates]}"
    )


def parent_blind_records(parent_root: Path):
    root = Path(parent_root)
    summary_path = root / "BLIND" / "summary.json"
    manifest_path = root / "BLIND" / "run_manifest.json"
    summary = _load_json(summary_path)
    manifest = _load_json(manifest_path)
    runs = list(summary.get("runs", []))
    if not runs:
        raise RuntimeError("v0.3.0 BLIND summary contains no runs")
    return summary, manifest, runs, {
        "parent_summary_sha256": sha256_file(summary_path),
        "parent_manifest_sha256": sha256_file(manifest_path),
    }


def _geom_rows(runs):
    by = {}
    for r in runs:
        gid = str(r["geometry_id"])
        by.setdefault(gid, []).append(r)
    records = []
    for gid, rows in sorted(by.items()):
        valid = [r for r in rows if r.get("numerically_valid")]
        pool = valid or rows
        # v0.3.0 normally has one population replay per geometry.  If more exist,
        # use the replay with the strongest late-window R^2 without pooling values.
        def key(r):
            fit = r.get("blowup_fit") or {}
            return (float(fit.get("r2") or -1e99), float(r.get("omega_growth") or -1e99))
        row = max(pool, key=key)
        fit = row.get("blowup_fit") or {}
        tstar = fit.get("t_star")
        rec = {
            "geometry_id": gid,
            "group_id": str(row.get("group_id") or "group_unspecified"),
            "parent_case_id": row.get("case_id"),
            "omega_growth": float(row.get("omega_growth") or 0.0),
            "fit_r2": float(fit.get("r2") or 0.0),
            "t_star": None if tstar is None else float(tstar),
            "T": float(row.get("T") or 0.0),
            "numerically_valid": bool(row.get("numerically_valid")),
        }
        records.append(rec)
    return records


def select_parent_blind(parent_root: Path, policy: dict | None = None):
    """Deterministically select follow-up geometries using BLIND v0.3.0 data only.

    No carrier/source/variant information is read in this function.  The returned
    selection can therefore be frozen and hashed before the REVEALED map is opened.
    """
    policy = dict(policy or {})
    max_geometries = int(policy.get("max_geometries", 8))
    if max_geometries < 1:
        raise ValueError("max_geometries must be >=1")
    summary, manifest, runs, hashes = parent_blind_records(parent_root)
    records = _geom_rows(runs)
    valid = [r for r in records if r["numerically_valid"]]
    if not valid:
        raise RuntimeError("v0.3.0 has no numerically valid geometries")

    selected = []
    reasons = {}

    def add(rec, reason):
        gid = rec["geometry_id"]
        if gid not in reasons and len(selected) < max_geometries:
            selected.append(rec)
            reasons[gid] = reason

    # S00-A: one representative from every anonymous independence group.
    groups = {}
    for r in valid:
        groups.setdefault(r["group_id"], []).append(r)
    for group in sorted(groups):
        rec = max(groups[group], key=lambda r: (r["omega_growth"], r["fit_r2"], r["geometry_id"]))
        add(rec, "mandatory_group_representative_max_growth")

    remaining = lambda: [r for r in valid if r["geometry_id"] not in reasons]

    # S00-B/C/D: orthogonal anomaly criteria, all based on blind observables.
    rr = remaining()
    if rr:
        add(max(rr, key=lambda r: (r["fit_r2"], r["omega_growth"], r["geometry_id"])), "global_best_inverse_omega_fit")
    rr = [r for r in remaining() if r["t_star"] is not None and r["t_star"] > r["T"]]
    if rr:
        add(min(rr, key=lambda r: (r["t_star"], -r["fit_r2"], r["geometry_id"])), "earliest_positive_future_tstar")
    rr = remaining()
    if rr:
        add(max(rr, key=lambda r: (r["omega_growth"], r["fit_r2"], r["geometry_id"])), "global_max_growth")

    # Deterministic controls if criteria overlap and free slots remain.
    while len(selected) < min(max_geometries, len(valid)):
        rr = remaining()
        if not rr:
            break
        growths = sorted(r["omega_growth"] for r in valid)
        median = growths[len(growths)//2]
        if len(selected) % 2 == 0:
            rec = min(rr, key=lambda r: (abs(r["omega_growth"] - median), r["geometry_id"]))
            add(rec, "median_growth_control")
        else:
            rec = min(rr, key=lambda r: (r["omega_growth"], r["geometry_id"]))
            add(rec, "low_growth_control")

    out_rows = []
    for rank, r in enumerate(selected, 1):
        q = dict(r)
        q["selection_rank"] = rank
        q["selection_reason"] = reasons[r["geometry_id"]]
        out_rows.append(q)

    frozen = {
        "schema": "A047-V040-PARENT-BLIND-SELECTION-1",
        "parent_version": "v0.3.0",
        "parent_verdict": (summary.get("assessment") or {}).get("verdict"),
        "parent_geometry_count": len(records),
        "parent_valid_geometry_count": len(valid),
        "anonymous_group_count": len(groups),
        "policy": policy,
        "selected_count": len(out_rows),
        "selected": out_rows,
        **hashes,
    }
    payload = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    frozen["selection_sha256"] = hashlib.sha256(payload).hexdigest()
    return frozen


def reveal_parent_selection(parent_root: Path, frozen_selection: dict):
    """Map already-frozen anonymous geometry IDs onto v0.3.0 carrier IDs."""
    reveal_path = Path(parent_root) / "REVEALED" / "case_reveal_map.json"
    reveal = _load_json(reveal_path)
    rows = []
    for s in frozen_selection.get("selected", []):
        gid = s["geometry_id"]
        rec = reveal.get(gid)
        if not isinstance(rec, dict) or not rec.get("e010_carrier_id"):
            raise RuntimeError(f"parent reveal map has no E010 carrier for {gid}")
        rows.append({
            "geometry_id": gid,
            "group_id": s["group_id"],
            "selection_rank": s["selection_rank"],
            "selection_reason": s["selection_reason"],
            "e010_carrier_id": rec["e010_carrier_id"],
        })
    return {
        "schema": "A047-V040-PARENT-SELECTION-REVEAL-1",
        "selection_sha256": frozen_selection["selection_sha256"],
        "parent_reveal_sha256": sha256_file(reveal_path),
        "selected": rows,
    }
