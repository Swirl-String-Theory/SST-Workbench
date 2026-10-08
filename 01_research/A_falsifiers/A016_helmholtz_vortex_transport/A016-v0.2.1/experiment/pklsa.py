from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import numpy as np

from sst_falsifier.source_registry import workbench_root

from .io import load_centerline, sha256_file


EXPECTED_RELEASE_SCHEMA = "PKLSA-HIGH-RES-QUALIFICATION-4"
EXPECTED_ATLAS_VERSION = "0.4.0"
_GENERATED_FAMILIES = {
    "ptsa", "ptsa_control", "ptsa_braid", "siaf",
    "katlas_braid_derived", "katlas_source_derived", "knot_library_derived",
}


@dataclass(frozen=True)
class PKLSACarrier:
    topology_id: str
    carrier_id: str
    source_family: str
    provenance_family: str
    independence_group: str
    provider_group: str
    source_role: str
    representation: str
    generated: bool
    geometry_sha256: str
    source_file_sha256: str
    source_path: Path
    descriptor_path: Path
    qualification_summary_path: Path


class PKLSAError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise PKLSAError(f"expected JSON object: {path}")
    return obj


def _source_spec(instance_root: Path) -> dict[str, Any]:
    contract = _read_json(instance_root / "source_contract.json")
    matches = [s for s in contract.get("sources", []) if s.get("source_id") == "S0_PKLSA_V040"]
    if len(matches) != 1:
        raise PKLSAError("source_contract.json must contain exactly one S0_PKLSA_V040 source")
    return matches[0]


def resolve_pklsa_version_root(instance_root: Path) -> Path:
    src = _source_spec(instance_root)
    if src.get("override_path"):
        return Path(src["override_path"]).expanduser()
    rel = src.get("relative_path")
    if not rel:
        raise PKLSAError("PKLSA source requires relative_path or override_path")
    return workbench_root() / rel


def _release_candidates(pklsa_root: Path, source_spec: dict[str, Any]) -> list[Path]:
    rel = source_spec.get("release_relative_path")
    if rel:
        return [pklsa_root / rel]
    # Allow output folder naming to evolve while requiring a unique release record.
    candidates = []
    for p in pklsa_root.rglob("RELEASE.json"):
        try:
            depth = len(p.relative_to(pklsa_root).parts)
        except ValueError:
            continue
        if depth <= int(source_spec.get("release_search_max_depth", 6)):
            candidates.append(p)
    return sorted(set(candidates), key=lambda p: p.as_posix().casefold())


def resolve_release(instance_root: Path) -> tuple[Path, dict[str, Any], Path]:
    src = _source_spec(instance_root)
    pklsa_root = resolve_pklsa_version_root(instance_root)
    if not pklsa_root.is_dir():
        raise PKLSAError(f"PKLSA v0.4.0 root not found: {pklsa_root}")
    accepted: list[tuple[Path, dict[str, Any]]] = []
    rejected: list[str] = []
    for p in _release_candidates(pklsa_root, src):
        if not p.is_file():
            continue
        try:
            r = _read_json(p)
        except Exception as ex:
            rejected.append(f"{p}: {type(ex).__name__}: {ex}")
            continue
        if r.get("schema") == EXPECTED_RELEASE_SCHEMA and str(r.get("atlas_version")) == EXPECTED_ATLAS_VERSION:
            accepted.append((p, r))
    ready = [(p, r) for p, r in accepted if bool(r.get("publication_ready_geometry_layer"))]
    if len(ready) == 1:
        p, r = ready[0]
        return p, r, pklsa_root
    if len(ready) > 1:
        raise PKLSAError("multiple publication-ready PKLSA v0.4.0 RELEASE.json files found; pin release_relative_path in source_contract.json")
    if len(accepted) == 1:
        p, r = accepted[0]
        raise PKLSAError(f"PKLSA release exists but publication_ready_geometry_layer is false: {p}")
    if not accepted:
        extra = f"; rejected={rejected[:3]}" if rejected else ""
        raise PKLSAError(f"no PKLSA v0.4.0 {EXPECTED_RELEASE_SCHEMA} release found below {pklsa_root}{extra}")
    raise PKLSAError("PKLSA v0.4.0 releases were found but none is uniquely publication-ready")


def _topology_root_from_summary(summary_path: Path) -> Path:
    # <topology>/qualification/summary.json
    return summary_path.parent.parent


def _resolve_source_path(raw: str, *, descriptor: Path, topology_root: Path, atlas_root: Path, pklsa_root: Path) -> Path:
    p = Path(str(raw)).expanduser()
    candidates = [p] if p.is_absolute() else []
    if not p.is_absolute():
        candidates.extend([
            descriptor.parent / p,
            topology_root / p,
            atlas_root / p,
            pklsa_root / p,
            workbench_root() / p,
        ])
    # Some PKLSA records were created with absolute Workbench paths on another machine.
    # When the absolute path is stale, recover only by a suffix anchored at well-known
    # Workbench directories rather than filename-only search.
    if p.is_absolute() and not p.exists():
        parts = list(p.parts)
        for anchor in ("01_research", "02_libraries", "KnotPlot"):
            if anchor in parts:
                i = parts.index(anchor)
                candidates.append(workbench_root() / Path(*parts[i:]))
                break
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise PKLSAError(f"carrier source_path cannot be resolved: {raw!r} from {descriptor}")


def _generated(carrier: dict[str, Any], descriptor: Path, atlas_root: Path) -> bool:
    role = str(carrier.get("source_role") or "").casefold()
    sf = str(carrier.get("source_family") or "").casefold()
    pg = str(carrier.get("provider_group") or "").casefold()
    try:
        relparts = {x.casefold() for x in descriptor.relative_to(atlas_root).parts}
    except ValueError:
        relparts = set()
    return (
        role.startswith("generated")
        or sf in _GENERATED_FAMILIES
        or pg in {"sst_generated", "generated"}
        or "generated" in relparts
    )


def _descriptor_files(topology_root: Path) -> list[Path]:
    files: list[Path] = []
    for branch in ("sources", "generated"):
        d = topology_root / branch
        if d.is_dir():
            files.extend(p for p in d.rglob("*.json") if p.is_file())
    return sorted(files, key=lambda p: p.as_posix().casefold())


def discover_qualified_carriers(instance_root: Path) -> tuple[list[PKLSACarrier], dict[str, Any]]:
    release_path, release, pklsa_root = resolve_release(instance_root)
    atlas_root = release_path.parent
    summaries = sorted(atlas_root.rglob("qualification/summary.json"), key=lambda p: p.as_posix().casefold())
    carriers: list[PKLSACarrier] = []
    excluded_topologies: list[dict[str, Any]] = []
    descriptor_errors: list[dict[str, str]] = []

    for summary_path in summaries:
        try:
            summary = _read_json(summary_path)
        except Exception as ex:
            descriptor_errors.append({"path": str(summary_path), "error": f"{type(ex).__name__}: {ex}"})
            continue
        topology_root = _topology_root_from_summary(summary_path)
        topology_id = str(summary.get("topology_id") or topology_root.name)
        if not bool(summary.get("qualification_gate_pass")):
            excluded_topologies.append({"topology_id": topology_id, "reason": "qualification_gate_pass=false"})
            continue
        for descriptor in _descriptor_files(topology_root):
            try:
                payload = _read_json(descriptor)
                c = payload.get("carrier")
                if not isinstance(c, dict):
                    continue
                carrier_id = str(c.get("carrier_id") or "").strip()
                source_family = str(c.get("source_family") or "").strip()
                source_path_raw = c.get("source_path")
                if not carrier_id or not source_family or not source_path_raw:
                    raise PKLSAError("descriptor missing carrier_id, source_family, or source_path")
                source_path = _resolve_source_path(
                    str(source_path_raw), descriptor=descriptor, topology_root=topology_root,
                    atlas_root=atlas_root, pklsa_root=pklsa_root,
                )
                geometry_sha = str(payload.get("geometry_sha256") or c.get("geometry_sha256") or "").strip()
                if not geometry_sha:
                    # Raw file hash is a fallback identity only; PKLSA-native geometry hash is preferred.
                    geometry_sha = sha256_file(source_path)
                source_role = str(c.get("source_role") or "unknown")
                parent_family = str(c.get("parent_source_family") or "").strip()
                provenance_family = parent_family or source_family
                provider_group = str(c.get("provider_group") or provenance_family or source_family)
                independence_group = str(c.get("independence_group") or f"{provider_group}:{geometry_sha}")
                rep = str(c.get("representation") or source_path.suffix.lstrip(".") or "unknown")
                carriers.append(PKLSACarrier(
                    topology_id=str(c.get("topology_id") or topology_id),
                    carrier_id=carrier_id,
                    source_family=source_family,
                    provenance_family=provenance_family,
                    independence_group=independence_group,
                    provider_group=provider_group,
                    source_role=source_role,
                    representation=rep,
                    generated=_generated(c, descriptor, atlas_root),
                    geometry_sha256=geometry_sha,
                    source_file_sha256=sha256_file(source_path),
                    source_path=source_path,
                    descriptor_path=descriptor.resolve(),
                    qualification_summary_path=summary_path.resolve(),
                ))
            except Exception as ex:
                descriptor_errors.append({"path": str(descriptor), "error": f"{type(ex).__name__}: {ex}"})

    # Exact duplicate descriptors do not create new evidence units.
    dedup: dict[tuple[str, str, str, str], PKLSACarrier] = {}
    for c in carriers:
        k = (c.topology_id, c.source_family, c.independence_group, c.geometry_sha256)
        dedup.setdefault(k, c)
    carriers = sorted(dedup.values(), key=lambda c: (
        c.topology_id.casefold(), c.provider_group.casefold(), c.source_family.casefold(), c.carrier_id.casefold()
    ))

    meta = {
        "release_path": str(release_path.resolve()),
        "release_sha256": sha256_file(release_path),
        "release_schema": release.get("schema"),
        "atlas_version": release.get("atlas_version"),
        "builder_version": release.get("builder_version"),
        "publication_ready_geometry_layer": bool(release.get("publication_ready_geometry_layer")),
        "n_qualification_summaries": len(summaries),
        "n_qualified_carriers": len(carriers),
        "n_upstream_carriers": sum(not c.generated for c in carriers),
        "n_generated_carriers": sum(c.generated for c in carriers),
        "n_excluded_topologies": len(excluded_topologies),
        "n_descriptor_errors": len(descriptor_errors),
        "excluded_topologies": excluded_topologies,
        "descriptor_errors": descriptor_errors,
        "scientific_boundary": release.get("scientific_boundary"),
    }
    return carriers, meta


def _normalize_components(comps: list[np.ndarray], path: Path) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    for raw in comps:
        p = np.asarray(raw, dtype=np.float64)
        if p.ndim != 2 or p.shape[1] < 3:
            continue
        p = p[:, :3]
        finite = np.all(np.isfinite(p), axis=1)
        p = p[finite]
        if len(p) < 3:
            continue
        scale = max(1.0, float(np.ptp(p, axis=0).max()))
        if len(p) > 3 and np.linalg.norm(p[0] - p[-1]) < 1e-12 * scale:
            p = p[:-1]
        if len(p) >= 3:
            out.append(np.ascontiguousarray(p, dtype=np.float64))
    if not out:
        raise PKLSAError(f"no XYZ components found in PKLSA carrier {path}")
    return out


def load_pklsa_geometry(path: str | Path) -> list[np.ndarray]:
    p = Path(path)
    ext = p.suffix.casefold()
    if ext == ".npz":
        with np.load(p, allow_pickle=False) as z:
            keys = sorted(z.files, key=lambda k: (0 if k.startswith("component_") else 1, k))
            comps = []
            if any(k.startswith("component_") for k in keys):
                comps = [np.asarray(z[k], dtype=np.float64) for k in keys if k.startswith("component_")]
            elif "points" in z.files:
                comps = [np.asarray(z["points"], dtype=np.float64)]
            return _normalize_components(comps, p)
    if ext == ".npy":
        return _normalize_components([np.load(p, allow_pickle=False)], p)
    if ext == ".json":
        obj = json.loads(p.read_text(encoding="utf-8"))
        candidates: list[Any] = []
        if isinstance(obj, dict):
            for key in ("components", "centerlines", "curves"):
                if isinstance(obj.get(key), list):
                    candidates = obj[key]
                    break
            if not candidates:
                for key in ("points", "xyz", "centerline"):
                    if isinstance(obj.get(key), list):
                        candidates = [obj[key]]
                        break
        elif isinstance(obj, list):
            candidates = [obj]
        return _normalize_components([np.asarray(x, dtype=np.float64) for x in candidates], p)
    return load_centerline(p)


def stratified_limit(carriers: list[PKLSACarrier], max_count: int) -> list[PKLSACarrier]:
    if max_count <= 0 or len(carriers) <= max_count:
        return list(carriers)
    # Round-robin first over topology then provider group so BASIC does not accidentally
    # sample only one provider and make the cross-source gate structurally unresolved.
    buckets: dict[tuple[str, str], list[PKLSACarrier]] = {}
    for c in carriers:
        buckets.setdefault((c.topology_id, c.provider_group), []).append(c)
    for v in buckets.values():
        v.sort(key=lambda c: (c.generated, c.source_family.casefold(), c.carrier_id.casefold()))
    keys = sorted(buckets, key=lambda x: (x[0].casefold(), x[1].casefold()))
    out: list[PKLSACarrier] = []
    while len(out) < max_count:
        progressed = False
        for k in keys:
            if buckets[k] and len(out) < max_count:
                out.append(buckets[k].pop(0)); progressed = True
        if not progressed:
            break
    return out
