from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib
import json
import os
import sys
from typing import Iterable

import numpy as np

E010_VERSION = "0.3.1"
TOPOLOGY_ID = "3_1"
E010_RELATIVE_ROOT = Path("01_research") / "E_pipelines" / "E010_pklsa_parametric_knot_link_seed_atlas" / "E010-v0.3.1"
E010_OUTPUT_NAME = "E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs"

CORE_RELEASE_GATES = (
    "source_contract_gate_pass",
    "a001_a008_coverage_gate_pass",
    "canonical_identity_admission_gate_pass",
    "identity_database_gate_pass",
    "topology_database_ingest_gate_pass",
    "trefoil_poc_gate_pass",
)

EXCLUDED_EVIDENCE_CLASSES = {
    "BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT",
    "MIRROR_NOT_INDEPENDENT",
}


@dataclass(frozen=True)
class E010Carrier:
    carrier_id: str
    source_family: str
    source_role: str
    representation: str
    source_path: str
    raw_sha256: str | None
    geometry_sha256: str
    independence_group: str | None
    provider_group: str | None
    lineage_group: str | None
    method_group: str | None
    evidence_independence_class: str | None
    catalog_id: str | None
    variant_id: str | None
    parent_source_family: str | None
    metadata: dict
    envelope_path: str
    literature_hard_gate_pass: bool | None
    literature_gate_status: dict
    geometry_duplicate_of: str | None
    raw_duplicate_of: str | None
    contributes_new_upstream_provider: bool
    reach: float | None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def geometry_sha256(components: Iterable[np.ndarray]) -> str:
    """Exact E010 PKLSA-GEOMETRY-SHA256-v1 contract."""
    h = hashlib.sha256()
    h.update(b"PKLSA-GEOMETRY-SHA256-v1\0")
    for c in components:
        a = np.asarray(c, dtype="<f8", order="C")
        h.update(np.asarray(a.shape, dtype="<i8").tobytes())
        h.update(a.tobytes(order="C"))
    return h.hexdigest()


def resolve_workbench_root(arg: str | None) -> Path:
    value = arg or os.environ.get("SST_WORKBENCH_ROOT") or r"C:\workspace\projects\SST-Workbench"
    p = Path(value).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"SST-Workbench root does not exist: {p}")
    return p


def locate_e010(workbench_root: Path, e010_root: str | Path | None = None, e010_output: str | Path | None = None):
    wb = Path(workbench_root).resolve()
    eroot = Path(e010_root).resolve() if e010_root else (wb / E010_RELATIVE_ROOT)
    out = Path(e010_output).resolve() if e010_output else (eroot / E010_OUTPUT_NAME)
    if not eroot.is_dir():
        raise FileNotFoundError(f"E010 PKLSA v{E010_VERSION} root missing: {eroot}")
    if not out.is_dir():
        raise FileNotFoundError(f"E010 PKLSA v{E010_VERSION} production outputs missing: {out}")
    return eroot, out


def _read_json(path: Path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def validate_e010_release(output_root: Path, require_core_gates: bool = True):
    p = Path(output_root) / "RELEASE.json"
    if not p.exists():
        raise FileNotFoundError(f"E010 production RELEASE.json missing: {p}")
    release = _read_json(p)
    if str(release.get("e010_version")) != E010_VERSION:
        raise RuntimeError(f"expected E010 v{E010_VERSION}, got {release.get('e010_version')!r}")
    if release.get("source_native_mode") is not True:
        raise RuntimeError("E010 v0.3.1 output is not source-native")
    if require_core_gates:
        failed = [k for k in CORE_RELEASE_GATES if release.get(k) is not True]
        if failed:
            raise RuntimeError(f"E010 core release gates failed: {failed}")
    # Deliberately do not require aggregate publication_ready_geometry_layer/full_campaign_gate_pass:
    # A047 consumes the independently qualified 3_1 POC, not all 2227 topologies.
    return release


def load_trefoil_contract(output_root: Path):
    top = Path(output_root) / "poc" / "atlas" / TOPOLOGY_ID
    qdir = top / "qualification"
    summary_p = qdir / "summary.json"
    indep_p = qdir / "source_independence.json"
    metrics_p = qdir / "geometry_metrics.json"
    for p in (summary_p, indep_p, metrics_p):
        if not p.exists():
            raise FileNotFoundError(f"E010 trefoil POC artifact missing: {p}")
    summary = _read_json(summary_p)
    indep = _read_json(indep_p)
    metrics = _read_json(metrics_p)
    if summary.get("topology_id") != TOPOLOGY_ID:
        raise RuntimeError("E010 POC topology is not 3_1")
    if summary.get("qualification_gate_pass") is not True:
        raise RuntimeError("E010 3_1 qualification gate is not green")
    if int(summary.get("error_carriers", -1)) != 0:
        raise RuntimeError("E010 3_1 POC contains carrier qualification errors")
    if int(summary.get("discovered_carriers", -1)) != int(summary.get("qualified_carriers", -2)):
        raise RuntimeError("E010 3_1 discovered/qualified carrier counts disagree")
    if int(indep.get("carrier_count", -1)) != int(summary.get("qualified_carriers", -2)):
        raise RuntimeError("E010 3_1 independence ledger count disagrees with summary")
    if int(metrics.get("record_count", -1)) != int(summary.get("qualified_carriers", -2)):
        raise RuntimeError("E010 3_1 geometry-metrics count disagrees with summary")
    return top, summary, indep, metrics


def _carrier_envelopes(topology_root: Path):
    records = {}
    for parent in (Path(topology_root) / "sources", Path(topology_root) / "generated"):
        for p in sorted(parent.rglob("CAR_*.json")):
            obj = _read_json(p)
            c = obj.get("carrier") or {}
            cid = c.get("carrier_id")
            if not cid:
                raise RuntimeError(f"carrier envelope has no carrier_id: {p}")
            if cid in records:
                raise RuntimeError(f"duplicate carrier envelope for {cid}")
            records[cid] = (p, obj)
    return records


def select_trefoil_carriers(output_root: Path, selection: dict | None = None):
    selection = dict(selection or {})
    top, summary, indep, metrics = load_trefoil_contract(output_root)
    envelopes = _carrier_envelopes(top)
    indep_by_id = {e["carrier_id"]: e for e in indep.get("entries", [])}
    metrics_by_id = {e["carrier_id"]: e for e in metrics.get("carriers", [])}
    hard_failures = set(summary.get("literature_hard_gate_failures", []))

    if set(envelopes) != set(indep_by_id) or set(envelopes) != set(metrics_by_id):
        missing = sorted((set(indep_by_id) | set(metrics_by_id)) - set(envelopes))[:10]
        extra = sorted(set(envelopes) - (set(indep_by_id) & set(metrics_by_id)))[:10]
        raise RuntimeError(f"E010 carrier ledger/envelope mismatch; missing={missing}, extra={extra}")

    literature_policy = str(selection.get("literature_gate_policy", "exclude_hard_fail"))
    duplicate_policy = str(selection.get("duplicate_policy", "geometry_and_raw_unique"))
    requested_families = selection.get("source_families", "all")
    requested_families = None if requested_families in (None, "all") else set(map(str, requested_families))
    excluded_classes = set(selection.get("exclude_evidence_classes", sorted(EXCLUDED_EVIDENCE_CLASSES)))
    max_per_group = int(selection.get("max_per_independence_group", 0) or 0)

    selected = []
    reasons = {}
    group_counts = {}
    for cid in sorted(envelopes):
        p, obj = envelopes[cid]
        c = obj["carrier"]
        ie = indep_by_id[cid]
        me = metrics_by_id[cid]
        reason = None
        if c.get("topology_id") != TOPOLOGY_ID or ie.get("topology_id") != TOPOLOGY_ID:
            reason = "wrong_topology"
        elif requested_families is not None and c.get("source_family") not in requested_families:
            reason = "source_family_filter"
        elif ie.get("evidence_independence_class") in excluded_classes:
            reason = "nonindependent_mirror"
        elif literature_policy == "exclude_hard_fail" and (cid in hard_failures or me.get("literature_hard_gate_pass") is False):
            reason = "literature_hard_gate_fail"
        elif literature_policy == "require_pass" and me.get("literature_hard_gate_pass") is not True:
            reason = "literature_hard_gate_not_pass"
        elif literature_policy not in ("exclude_hard_fail", "require_pass", "report_only"):
            raise ValueError(f"unknown literature_gate_policy={literature_policy!r}")
        elif duplicate_policy == "geometry_and_raw_unique" and (ie.get("geometry_duplicate_of") or ie.get("raw_duplicate_of")):
            reason = "duplicate_geometry_or_raw"
        elif duplicate_policy == "geometry_unique" and ie.get("geometry_duplicate_of"):
            reason = "duplicate_geometry"
        elif duplicate_policy not in ("geometry_and_raw_unique", "geometry_unique", "keep_all"):
            raise ValueError(f"unknown duplicate_policy={duplicate_policy!r}")

        group = ie.get("independence_group") or "UNSPECIFIED"
        if reason is None and max_per_group and group_counts.get(group, 0) >= max_per_group:
            reason = "independence_group_cap"

        if reason is not None:
            reasons[cid] = reason
            continue

        group_counts[group] = group_counts.get(group, 0) + 1
        selected.append(E010Carrier(
            carrier_id=cid,
            source_family=str(c.get("source_family")),
            source_role=str(c.get("source_role")),
            representation=str(c.get("representation")),
            source_path=str(c.get("source_path") or ""),
            raw_sha256=c.get("raw_sha256"),
            geometry_sha256=str(obj.get("geometry_sha256") or ""),
            independence_group=ie.get("independence_group"),
            provider_group=ie.get("provider_group"),
            lineage_group=ie.get("lineage_group"),
            method_group=ie.get("method_group"),
            evidence_independence_class=ie.get("evidence_independence_class"),
            catalog_id=c.get("catalog_id"),
            variant_id=c.get("variant_id"),
            parent_source_family=c.get("parent_source_family"),
            metadata=dict(c.get("metadata") or {}),
            envelope_path=str(p),
            literature_hard_gate_pass=me.get("literature_hard_gate_pass"),
            literature_gate_status=dict(me.get("literature_gate_status") or {}),
            geometry_duplicate_of=ie.get("geometry_duplicate_of"),
            raw_duplicate_of=ie.get("raw_duplicate_of"),
            contributes_new_upstream_provider=bool(ie.get("contributes_new_upstream_provider",False)),
            reach=float(me.get("reach")) if me.get("reach") is not None else None,
        ))

    if not selected:
        raise RuntimeError("E010 selection produced zero 3_1 carriers")
    audit = {
        "qualified_input_count": int(summary["qualified_carriers"]),
        "selected_count": len(selected),
        "excluded_count": len(reasons),
        "excluded_by_reason": {r: sum(v == r for v in reasons.values()) for r in sorted(set(reasons.values()))},
        "selected_independence_group_count": len(group_counts),
        "selection": selection,
    }
    return selected, audit, summary


def _root_relative_from_windows_string(path_string: str):
    s = str(path_string).replace("/", "\\")
    marker = "\\SST-Workbench\\"
    i = s.lower().find(marker.lower())
    if i < 0:
        return None
    return Path(*[x for x in s[i + len(marker):].split("\\") if x])


def resolve_carrier_source_path(carrier: E010Carrier, workbench_root: Path) -> Path:
    raw = carrier.source_path
    if raw:
        p = Path(raw)
        if p.exists():
            return p.resolve()
        rel = _root_relative_from_windows_string(raw)
        if rel is not None:
            q = Path(workbench_root) / rel
            if q.exists(): return q.resolve()

    md = carrier.metadata or {}
    source_root = md.get("source_root")
    relative_path = md.get("relative_path")
    if source_root and relative_path:
        rel_root = _root_relative_from_windows_string(str(source_root))
        if rel_root is not None:
            q = Path(workbench_root) / rel_root / Path(str(relative_path).replace("\\", "/"))
            if q.exists(): return q.resolve()
    raise FileNotFoundError(f"source bytes for {carrier.carrier_id} are not resolvable from Workbench root")


@contextmanager
def _e010_import_path(e010_root: Path):
    root = str(Path(e010_root).resolve())
    old = list(sys.path)
    try:
        if root not in sys.path: sys.path.insert(0, root)
        yield
    finally:
        sys.path[:] = old


def load_carrier_centerline(carrier: E010Carrier, workbench_root: Path, e010_root: Path,
                            strict_raw_hash: bool = True, strict_geometry_hash: bool = True):
    source = resolve_carrier_source_path(carrier, workbench_root)
    raw_digest = sha256_file(source)
    if strict_raw_hash and carrier.raw_sha256 and raw_digest != carrier.raw_sha256:
        raise RuntimeError(f"raw source SHA256 mismatch for {carrier.carrier_id}: {raw_digest} != {carrier.raw_sha256}")

    with _e010_import_path(e010_root):
        io_geometry = importlib.import_module("pklsa_builder.io_geometry")
        gilbert = importlib.import_module("pklsa_builder.gilbert")
        if carrier.representation == "gilbert_ab_record":
            record = gilbert.find_gilbert_record(source, TOPOLOGY_ID)
            comps = gilbert.sample_gilbert_components(record, n=max(4096, int(carrier.metadata.get("native_sample_n", 4096) or 4096)))
        else:
            comps = io_geometry.load_geometry(source, representation=carrier.representation)

    comps = [np.asarray(c, dtype=float) for c in comps]
    if len(comps) != 1:
        raise RuntimeError(f"3_1 carrier {carrier.carrier_id} resolved to {len(comps)} components, expected 1")
    if comps[0].ndim != 2 or comps[0].shape[1] != 3 or len(comps[0]) < 8 or not np.isfinite(comps[0]).all():
        raise RuntimeError(f"invalid 3_1 centerline for {carrier.carrier_id}: shape={comps[0].shape}")
    gh = geometry_sha256(comps)
    if strict_geometry_hash and carrier.geometry_sha256 and gh != carrier.geometry_sha256:
        raise RuntimeError(f"E010 geometry SHA256 mismatch for {carrier.carrier_id}: {gh} != {carrier.geometry_sha256}")
    return comps[0].copy(), {"resolved_source_path": str(source), "raw_sha256": raw_digest, "geometry_sha256": gh}


def closed_arclength_resample(points, n: int):
    P = np.asarray(points, float)
    if P.ndim != 2 or P.shape[1] != 3 or len(P) < 8:
        raise ValueError("expected centerline shape (M,3), M>=8")
    Q = np.vstack([P, P[0]])
    seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    if not np.isfinite(seg).all() or np.any(seg <= 0):
        raise ValueError("degenerate/non-finite centerline segments")
    s = np.concatenate([[0.0], np.cumsum(seg)])
    targets = np.linspace(0.0, s[-1], int(n), endpoint=False)
    return np.column_stack([np.interp(targets, s, Q[:, j]) for j in range(3)])


def canonicalize_centerline(points, n: int, target_rms_radius: float):
    P = closed_arclength_resample(points, n)
    centroid = P.mean(axis=0)
    P = P - centroid
    rms = float(np.sqrt(np.mean(np.sum(P * P, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("invalid centerline RMS radius")
    scale = float(target_rms_radius) / rms
    P = P * scale
    raw = np.ascontiguousarray(np.asarray(points, dtype=np.float64))
    canon = np.ascontiguousarray(P, dtype=np.float64)
    return P, {
        "raw_coordinate_sha256": hashlib.sha256(raw.tobytes()).hexdigest(),
        "canonical_coordinate_sha256": hashlib.sha256(canon.tobytes()).hexdigest(),
        "input_points": int(len(raw)),
        "resampled_points": int(len(P)),
        "input_centroid": [float(x) for x in centroid],
        "input_rms_radius": rms,
        "scale_to_target": scale,
        "target_rms_radius": float(target_rms_radius),
        "transform": "closed-arclength resample -> centroid removal -> uniform RMS-radius scale; no rotation or reflection",
    }


def strict_provider_representatives(output_root: Path):
    carriers,audit,summary=select_trefoil_carriers(output_root,{
        "literature_gate_policy":"require_pass",
        "duplicate_policy":"geometry_and_raw_unique",
        "exclude_evidence_classes":sorted(EXCLUDED_EVIDENCE_CLASSES),
    })
    reps=[c for c in carriers if c.contributes_new_upstream_provider]
    providers={c.provider_group for c in reps if c.provider_group}
    if len(reps)<2 or len(providers)<2:
        raise RuntimeError(f"strict provider rule requires >=2 E010 new-upstream-provider representatives, got carriers={len(reps)} providers={sorted(providers)}")
    reps=sorted(reps,key=lambda c:(str(c.provider_group),c.carrier_id))
    audit={**audit,"strict_provider_representative_count":len(reps),"strict_provider_groups":sorted(providers)}
    return reps,audit,summary
