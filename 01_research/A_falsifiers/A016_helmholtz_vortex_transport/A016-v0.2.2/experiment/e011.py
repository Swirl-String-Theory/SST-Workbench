from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Any
import gzip
import hashlib
import json
import re
import zipfile

import numpy as np

from sst_falsifier.source_registry import workbench_root


EXPECTED_E011_SUMMARY_SCHEMA = "E011-SKLSA-STATIC-READY-ATLAS-1"
EXPECTED_E011_VERSION = "0.3.0"
EXPECTED_SEED_SCHEMA = "E011-STATIC-SEED-CONTRACT-1"
EXPECTED_E010_SCHEMA = "E010-PKLSA-PRODUCTION-KNOT-LINK-BASIS-1"
EXPECTED_E010_VERSION = "0.3.1"
ALLOWED_REPRESENTATIONS = {"xyz", "vect", "gilbert_ab_record"}


@dataclass(frozen=True)
class E011Carrier:
    topology_id: str
    carrier_id: str
    static_seed_id: str
    source_family: str
    provenance_family: str
    independence_group: str
    provider_group: str
    source_role: str
    representation: str
    generated: bool
    geometry_sha256: str
    source_file_sha256: str
    reference_id: str | None
    source_path: Path
    seed_manifest: str
    evidence_class: str


class E011Error(RuntimeError):
    pass


_RAW_HASH_CACHE: dict[str, str] = {}


def _sha256_file(path: Path) -> str:
    key = str(path.resolve())
    if key in _RAW_HASH_CACHE:
        return _RAW_HASH_CACHE[key]
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    out = h.hexdigest()
    _RAW_HASH_CACHE[key] = out
    return out


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise E011Error(f"expected JSON object: {path}")
    return obj


def _source_spec(instance_root: Path) -> dict[str, Any]:
    contract = _read_json(instance_root / "source_contract.json")
    matches = [s for s in contract.get("sources", []) if s.get("source_id") == "S0_E011_STATIC_READY_V030"]
    if len(matches) != 1:
        raise E011Error("source_contract.json must contain exactly one S0_E011_STATIC_READY_V030 source")
    return matches[0]


def resolve_e011_version_root(instance_root: Path) -> Path:
    src = _source_spec(instance_root)
    if src.get("override_path"):
        return Path(src["override_path"]).expanduser()
    rel = src.get("relative_path")
    if not rel:
        raise E011Error("E011 source requires relative_path or override_path")
    return workbench_root() / rel


def _bundle_candidates(version_root: Path, spec: dict[str, Any]) -> list[Path]:
    exact_name = str(spec.get("outputs_relative_path") or "E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs")
    candidates = [version_root / exact_name]
    candidates.extend(sorted(version_root.glob("E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs")))
    candidates.extend(sorted(version_root.glob("E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip")))
    # Canonical Workbench archives are sometimes packed at the family root.
    candidates.extend(sorted(version_root.parent.glob("E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip")))
    out = []
    seen = set()
    for p in candidates:
        k = str(p.resolve()) if p.exists() else str(p)
        if k not in seen:
            seen.add(k); out.append(p)
    return out


def _zip_member(z: zipfile.ZipFile, basename: str) -> str:
    exact = [n for n in z.namelist() if PurePosixPath(n).name == basename and not n.endswith("/")]
    if len(exact) != 1:
        raise E011Error(f"E011 archive must contain exactly one {basename}; found {len(exact)}")
    return exact[0]


def _bundle_has(bundle: Path, basename: str) -> bool:
    if bundle.is_dir():
        return (bundle / basename).is_file()
    if bundle.is_file() and bundle.suffix.casefold() == ".zip":
        with zipfile.ZipFile(bundle, "r") as z:
            return len([n for n in z.namelist() if PurePosixPath(n).name == basename and not n.endswith("/")]) == 1
    return False


def _bundle_text(bundle: Path, basename: str) -> str:
    if bundle.is_dir():
        p = bundle / basename
        if not p.is_file():
            raise E011Error(f"missing E011 output file: {p}")
        return p.read_text(encoding="utf-8")
    if bundle.is_file() and bundle.suffix.casefold() == ".zip":
        with zipfile.ZipFile(bundle, "r") as z:
            member = _zip_member(z, basename)
            return z.read(member).decode("utf-8")
    raise E011Error(f"unsupported E011 output bundle: {bundle}")


def _bundle_json(bundle: Path, basename: str) -> dict[str, Any]:
    obj = json.loads(_bundle_text(bundle, basename))
    if not isinstance(obj, dict):
        raise E011Error(f"{basename} must contain one JSON object")
    return obj


def _bundle_jsonl(bundle: Path, basename: str) -> list[dict[str, Any]]:
    rows = []
    for lineno, raw in enumerate(_bundle_text(bundle, basename).splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue
        obj = json.loads(s)
        if not isinstance(obj, dict):
            raise E011Error(f"{basename}:{lineno} is not a JSON object")
        rows.append(obj)
    return rows


def resolve_e011_bundle(instance_root: Path) -> tuple[Path, Path]:
    spec = _source_spec(instance_root)
    version_root = resolve_e011_version_root(instance_root)
    if not version_root.is_dir():
        siblings = []
        parent = version_root.parent
        if parent.is_dir():
            siblings = sorted(p.name for p in parent.glob("E011-v*") if p.is_dir())
        hint = f"; found E011 versions={siblings}" if siblings else ""
        raise E011Error(f"E011-v0.3.0 root not found: {version_root}{hint}")
    required = ("RUN_SUMMARY.json", "SEED_CONTRACT_SCHEMA.json", "PARENT_RELEASE.json", "STATIC_READY_PROVIDER_ANCHORS.jsonl", "STATIC_READY_PRIMARY_SEEDS.jsonl")
    accepted = [p for p in _bundle_candidates(version_root, spec) if p.exists() and all(_bundle_has(p, n) for n in required)]
    if len(accepted) == 1:
        return accepted[0], version_root
    if len(accepted) > 1:
        # Prefer the unpacked canonical output directory when both directory and archive exist.
        dirs = [p for p in accepted if p.is_dir()]
        if len(dirs) == 1:
            return dirs[0], version_root
        raise E011Error(f"multiple E011-v0.3.0 STATIC_READY output bundles found: {[str(p) for p in accepted]}")
    raise E011Error(
        f"no complete E011-v0.3.0 STATIC_READY output bundle found below {version_root}; "
        "run E011-v0.3.0 first or restore E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs"
    )


def _validate_bundle(bundle: Path) -> dict[str, Any]:
    summary = _bundle_json(bundle, "RUN_SUMMARY.json")
    seed_contract = _bundle_json(bundle, "SEED_CONTRACT_SCHEMA.json")
    parent = _bundle_json(bundle, "PARENT_RELEASE.json")
    failures = []
    checks = {
        "summary_schema": summary.get("schema") == EXPECTED_E011_SUMMARY_SCHEMA,
        "e011_version": str(summary.get("e011_version")) == EXPECTED_E011_VERSION,
        "execution_gate": summary.get("execution_gate") == "PASS",
        "operational_error_count": int(summary.get("operational_error_count", -1)) == 0,
        "e010_release_version": str(summary.get("e010_release_version")) == EXPECTED_E010_VERSION,
        "seed_schema": seed_contract.get("schema") == EXPECTED_SEED_SCHEMA,
        "seed_atlas_version": str(seed_contract.get("atlas_version")) == EXPECTED_E011_VERSION,
        "seed_static_only": seed_contract.get("dynamics_ready") is False,
        "parent_schema": parent.get("schema") == EXPECTED_E010_SCHEMA,
        "parent_e010_version": str(parent.get("e010_version")) == EXPECTED_E010_VERSION,
        "parent_source_contract": bool(parent.get("source_contract_gate_pass")),
        "parent_topology_database": bool(parent.get("topology_database_ingest_gate_pass")),
        "parent_identity_database": bool(parent.get("identity_database_gate_pass")),
        "parent_identity_admission": bool(parent.get("canonical_identity_admission_gate_pass")),
    }
    for k, v in checks.items():
        if not v:
            failures.append(k)
    if failures:
        raise E011Error(f"E011 STATIC_READY bundle failed source-contract checks: {failures}")
    return {"summary": summary, "seed_contract": seed_contract, "parent_release": parent, "checks": checks}


def _anchored_suffix(raw: str) -> Path | None:
    # Handle both native and Windows absolute paths on any host.
    variants = [Path(raw).parts, PureWindowsPath(raw).parts]
    anchors = ("03_data", "01_research", "02_libraries", "04_tools", "KnotPlot")
    for parts in variants:
        for anchor in anchors:
            if anchor in parts:
                i = parts.index(anchor)
                return Path(*parts[i:])
    return None


def _resolve_source_path(raw: str) -> Path:
    p = Path(str(raw)).expanduser()
    candidates = []
    if p.is_absolute():
        candidates.append(p)
    suffix = _anchored_suffix(str(raw))
    if suffix is not None:
        candidates.append(workbench_root() / suffix)
    # Relative locator is always interpreted from Workbench root.
    if not p.is_absolute() and not PureWindowsPath(str(raw)).is_absolute():
        candidates.append(workbench_root() / p)
    seen = set()
    for c in candidates:
        k = str(c)
        if k in seen:
            continue
        seen.add(k)
        if c.is_file():
            return c.resolve()
    raise E011Error(f"E011 source_locator.source_path cannot be resolved: {raw!r}")


def _seed_to_carrier(seed: dict[str, Any], manifest_name: str) -> E011Carrier:
    if seed.get("static_ready") is not True:
        raise E011Error("seed is not static_ready=true")
    if seed.get("evidence_class") != "UPSTREAM_INDEPENDENT":
        raise E011Error(f"seed evidence_class is not UPSTREAM_INDEPENDENT: {seed.get('evidence_class')!r}")
    if seed.get("seed_role") != "PRIMARY_REFERENCE":
        raise E011Error(f"seed_role is not PRIMARY_REFERENCE: {seed.get('seed_role')!r}")
    loc = seed.get("source_locator")
    if not isinstance(loc, dict):
        raise E011Error("seed missing source_locator object")
    required = ("topology_id", "carrier_id", "static_seed_id", "provider_group", "source_family")
    missing = [k for k in required if not str(seed.get(k) or "").strip()]
    if missing:
        raise E011Error(f"seed missing fields: {missing}")
    rep = str(loc.get("representation") or "").strip().casefold()
    if rep not in ALLOWED_REPRESENTATIONS:
        raise E011Error(f"unsupported E011 representation {rep!r}; allowed={sorted(ALLOWED_REPRESENTATIONS)}")
    source_path = _resolve_source_path(str(loc.get("source_path") or ""))
    expected_raw = str(loc.get("raw_sha256") or "").strip().casefold()
    actual_raw = _sha256_file(source_path)
    if not expected_raw or expected_raw != actual_raw:
        raise E011Error(f"raw SHA-256 mismatch for {source_path}; expected={expected_raw or '<missing>'} actual={actual_raw}")
    geometry_sha = str(loc.get("geometry_sha256") or "").strip()
    if len(geometry_sha) != 64:
        raise E011Error("source_locator.geometry_sha256 missing or invalid")
    topology_id = str(seed["topology_id"])
    provider = str(seed["provider_group"])
    lineage = str(seed.get("lineage_group") or f"{provider}:{topology_id}")
    source_family = str(seed["source_family"])
    method_group = str(seed.get("method_group") or source_family)
    return E011Carrier(
        topology_id=topology_id,
        carrier_id=str(seed["carrier_id"]),
        static_seed_id=str(seed["static_seed_id"]),
        source_family=source_family,
        provenance_family=f"E011:{method_group}",
        independence_group=lineage,
        provider_group=provider,
        source_role=str(loc.get("source_role") or "upstream_static_ready"),
        representation=rep,
        generated=False,
        geometry_sha256=geometry_sha,
        source_file_sha256=actual_raw,
        reference_id=(str(loc.get("reference_id")) if loc.get("reference_id") is not None else None),
        source_path=source_path,
        seed_manifest=manifest_name,
        evidence_class=str(seed["evidence_class"]),
    )


def discover_static_ready_carriers(instance_root: Path, mode: str) -> tuple[list[E011Carrier], dict[str, Any]]:
    bundle, version_root = resolve_e011_bundle(instance_root)
    validated = _validate_bundle(bundle)
    manifest = "STATIC_READY_PRIMARY_SEEDS.jsonl" if mode.upper() == "CERTIFY" else "STATIC_READY_PROVIDER_ANCHORS.jsonl"
    rows = _bundle_jsonl(bundle, manifest)
    carriers: list[E011Carrier] = []
    errors: list[dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        try:
            carriers.append(_seed_to_carrier(row, manifest))
        except Exception as ex:
            errors.append({"row": i, "carrier_id": row.get("carrier_id"), "error": f"{type(ex).__name__}: {ex}"})
    # No duplicate evidence unit may enter the science loop.
    dedup: dict[tuple[str, str, str, str], E011Carrier] = {}
    for c in carriers:
        k = (c.topology_id, c.provider_group, c.independence_group, c.geometry_sha256)
        dedup.setdefault(k, c)
    carriers = sorted(dedup.values(), key=lambda c: (c.topology_id.casefold(), c.provider_group.casefold(), c.carrier_id.casefold()))
    summary = validated["summary"]
    meta = {
        "e011_version_root": str(version_root.resolve()),
        "bundle_path": str(bundle.resolve()),
        "bundle_kind": "directory" if bundle.is_dir() else "zip",
        "e011_summary_schema": summary.get("schema"),
        "e011_version": summary.get("e011_version"),
        "e011_execution_gate": summary.get("execution_gate"),
        "e011_operational_error_count": summary.get("operational_error_count"),
        "e010_release_version": summary.get("e010_release_version"),
        "static_ready_topology_count": summary.get("static_ready_topology_count"),
        "provider_anchor_count_declared": summary.get("provider_anchor_count"),
        "primary_static_seed_count_declared": summary.get("primary_static_seed_count"),
        "cross_provider_robust_topology_count": summary.get("cross_provider_robust_topology_count"),
        "cross_provider_sensitive_topology_count": summary.get("cross_provider_sensitive_topology_count"),
        "single_provider_qualified_topology_count": summary.get("single_provider_qualified_topology_count"),
        "selected_manifest": manifest,
        "n_manifest_rows": len(rows),
        "n_admitted_carriers": len(carriers),
        "n_distinct_topologies": len({c.topology_id for c in carriers}),
        "n_distinct_provider_groups": len({c.provider_group for c in carriers}),
        "n_multi_provider_topologies": sum(1 for t in {c.topology_id for c in carriers} if len({c.provider_group for c in carriers if c.topology_id == t}) >= 2),
        "n_source_errors": len(errors),
        "source_errors": errors,
        "validation_checks": validated["checks"],
        "parent_publication_ready_geometry_layer": bool(validated["parent_release"].get("publication_ready_geometry_layer")),
        "parent_full_campaign_gate_pass": bool(validated["parent_release"].get("full_campaign_gate_pass")),
        "scientific_boundary": summary.get("scientific_boundary"),
    }
    return carriers, meta


# ---- Geometry loaders. These reproduce the source-native dispatch used by E010-v0.3.1. ----

def _normalize_components(comps: list[np.ndarray], label: str) -> list[np.ndarray]:
    out: list[np.ndarray] = []
    for raw in comps:
        p = np.asarray(raw, dtype=np.float64)
        if p.ndim != 2 or p.shape[1] < 3:
            continue
        p = p[:, :3]
        p = p[np.all(np.isfinite(p), axis=1)]
        if len(p) < 3:
            continue
        scale = max(1.0, float(np.ptp(p, axis=0).max()))
        if len(p) > 3 and np.linalg.norm(p[0] - p[-1]) < 1e-12 * scale:
            p = p[:-1]
        if len(p) >= 3:
            out.append(np.ascontiguousarray(p, dtype=np.float64))
    if not out:
        raise E011Error(f"no XYZ components found in {label}")
    return out


def _load_xyz(path: Path) -> list[np.ndarray]:
    comps = []
    cur = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.strip()
        if not s:
            if cur:
                comps.append(np.asarray(cur, float)); cur = []
            continue
        if s.lower().startswith(("component", "curve", "vect")) or s.startswith(("#", "%", "//")):
            if s.lower().startswith(("component", "curve")) and cur:
                comps.append(np.asarray(cur, float)); cur = []
            continue
        vals = s.replace(",", " ").split()
        if len(vals) >= 3:
            try:
                cur.append([float(vals[0]), float(vals[1]), float(vals[2])])
            except ValueError:
                continue
    if cur:
        comps.append(np.asarray(cur, float))
    return _normalize_components(comps, str(path))


def _load_vect(path: Path) -> list[np.ndarray]:
    lines = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.split("#", 1)[0].strip()
        if s:
            lines.append(s)
    toks = " ".join(lines).split()
    if not toks or toks[0] not in ("VECT", "4VECT"):
        raise E011Error(f"not a Geomview VECT file: {path}")
    i = 1
    ncomp, nvert, _ncolor = int(toks[i]), int(toks[i+1]), int(toks[i+2]); i += 3
    counts = [int(toks[i+j]) for j in range(ncomp)]; i += ncomp
    i += ncomp  # color counts
    if sum(abs(x) for x in counts) != nvert:
        raise E011Error(f"VECT vertex count mismatch: {path}")
    comps = []
    for count in counts:
        pts = []
        for _ in range(abs(count)):
            pts.append([float(toks[i]), float(toks[i+1]), float(toks[i+2])]); i += 3
        a = np.asarray(pts, float)
        if count < 0 and len(a) > 1 and np.linalg.norm(a[0] - a[-1]) < 1e-14:
            a = a[:-1]
        comps.append(a)
    return _normalize_components(comps, str(path))


_ATTR_RE = re.compile(r'([A-Za-z_][A-Za-z0-9_.:-]*)\s*=\s*"([^"]*)"')
_RECORD_START_RE = re.compile(r'^\s*<(AB|HT|TL)\b([^>]*)>')
_COEFF_RE = re.compile(r'<Coeff\b([^>]*)/?>', re.I)
_STRING_RE = re.compile(r'<STRING\b([^>]*)>(.*?)</STRING\s*>', re.I | re.S)
_STRING_START_RE = re.compile(r'<STRING\b([^>]*)>', re.I)
_COLON_ID_RE = re.compile(r'^(\d+):(\d+):(\d+)$')
_HT_ID_RE = re.compile(r'^K(\d+)([an])(\d+)$', re.I)
_LINK_ID_RE = re.compile(r'^L(\d+)([an])(\d+)$', re.I)
_GILBERT_RAW_CACHE: dict[str, list[tuple[str, dict[str, str], str]]] = {}


def _attrs(text: str) -> dict[str, str]:
    return {k: v for k, v in _ATTR_RE.findall(text or "")}


def _canonical_id_from_gilbert(record_id: str | None) -> str | None:
    s = str(record_id or "").strip()
    m = _COLON_ID_RE.fullmatch(s)
    if m:
        crossings, namespace, index = map(int, m.groups())
        return f"{crossings}_{index}" if namespace == 1 else None
    m = _HT_ID_RE.fullmatch(s)
    if m:
        return f"{int(m.group(1))}{m.group(2).lower()}_{int(m.group(3))}"
    m = _LINK_ID_RE.fullmatch(s)
    if m:
        return f"L{int(m.group(1))}{m.group(2).lower()}{int(m.group(3))}"
    return None


def _read_gilbert_record_texts(path: Path) -> list[tuple[str, dict[str, str], str]]:
    key = str(path.resolve())
    if key in _GILBERT_RAW_CACHE:
        return _GILBERT_RAW_CACHE[key]
    opener = gzip.open if path.suffix.casefold() == ".gz" else open
    records = []
    with opener(path, "rt", encoding="utf-8", errors="strict") as f:
        active_tag = None; header_attrs = None; buf = []
        for line in f:
            if active_tag is None:
                m = _RECORD_START_RE.match(line)
                if not m:
                    continue
                active_tag = m.group(1).upper(); header_attrs = _attrs(m.group(2)); buf = [line[m.end():]]
                if re.search(fr'</{active_tag}\s*>', buf[0], re.I):
                    body = re.split(fr'</{active_tag}\s*>', buf[0], maxsplit=1, flags=re.I)[0]
                    records.append((active_tag, header_attrs, body)); active_tag = None; header_attrs = None; buf = []
                continue
            end_match = re.search(fr'</{active_tag}\s*>', line, re.I)
            if end_match:
                buf.append(line[:end_match.start()]); records.append((active_tag, header_attrs, "".join(buf)))
                active_tag = None; header_attrs = None; buf = []
            else:
                buf.append(line)
        if active_tag is not None:
            raise E011Error(f"unterminated Gilbert record <{active_tag}> in {path}")
    _GILBERT_RAW_CACHE[key] = records
    return records


def _parse_coefficients(text: str):
    out = []
    for raw in _COEFF_RE.findall(text or ""):
        a = _attrs(raw)
        if not {"I", "A", "B"} <= set(a):
            continue
        I = int(a["I"]); A = np.fromstring(a["A"], sep=",", dtype=float); B = np.fromstring(a["B"], sep=",", dtype=float)
        if A.shape != (3,) or B.shape != (3,):
            raise E011Error("Gilbert Coeff must contain 3-vectors A and B")
        out.append((I, A, B))
    return out


def _parse_gilbert_record(tag: str, header_attrs: dict[str, str], text: str) -> dict[str, Any]:
    record: dict[str, Any] = {"tag": tag, "attrs": header_attrs, "components": []}
    string_matches = list(_STRING_RE.finditer(text))
    if string_matches:
        for m in string_matches:
            coeff = _parse_coefficients(m.group(2))
            if coeff:
                record["components"].append({"attrs": _attrs(m.group(1)), "coeff": coeff})
    elif _STRING_START_RE.search(text):
        m = _STRING_START_RE.search(text)
        coeff = _parse_coefficients(text[m.end():])
        if coeff:
            record["components"].append({"attrs": _attrs(m.group(1)), "coeff": coeff})
    else:
        coeff = _parse_coefficients(text)
        if coeff:
            record["components"].append({"attrs": {}, "coeff": coeff})
    record["canonical_id"] = _canonical_id_from_gilbert(header_attrs.get("Id"))
    return record


def _find_gilbert_record(path: Path, topology_id: str) -> dict[str, Any]:
    for raw in _read_gilbert_record_texts(path):
        rec = _parse_gilbert_record(*raw)
        if rec.get("canonical_id") == topology_id:
            return rec
    raise E011Error(f"Gilbert topology {topology_id} not found in {path}")


def _sample_coefficients(coeff, n: int) -> np.ndarray:
    t = np.linspace(0, 2*np.pi, int(n), endpoint=False)
    out = np.zeros((int(n), 3), float)
    for I, A, B in coeff:
        if I == 0:
            out += 0.5 * A[None, :]
        else:
            out += np.cos(I*t)[:, None] * A[None, :] + np.sin(I*t)[:, None] * B[None, :]
    return out


def _load_gilbert(carrier: E011Carrier, n: int) -> list[np.ndarray]:
    record = _find_gilbert_record(carrier.source_path, carrier.topology_id)
    raw_id = str(record.get("attrs", {}).get("Id") or "")
    if carrier.reference_id and raw_id != carrier.reference_id:
        raise E011Error(
            f"Gilbert reference mismatch for {carrier.topology_id}: E011={carrier.reference_id!r}, source={raw_id!r}"
        )
    comps = record.get("components") or []
    if not comps:
        raise E011Error("Gilbert record contains no Fourier components")
    return _normalize_components([_sample_coefficients(c["coeff"], n) for c in comps], f"{carrier.source_path}#{raw_id}")


def load_e011_geometry(carrier: E011Carrier, *, n_hint: int = 4096) -> list[np.ndarray]:
    rep = carrier.representation.casefold()
    if rep == "gilbert_ab_record":
        return _load_gilbert(carrier, max(4096, int(n_hint)))
    if rep == "vect":
        return _load_vect(carrier.source_path)
    if rep == "xyz":
        return _load_xyz(carrier.source_path)
    raise E011Error(f"unsupported E011 representation: {rep}")


def stratified_limit(carriers: list[E011Carrier], max_count: int) -> list[E011Carrier]:
    if max_count <= 0 or len(carriers) <= max_count:
        return list(carriers)
    buckets: dict[tuple[str, str], list[E011Carrier]] = {}
    for c in carriers:
        buckets.setdefault((c.topology_id, c.provider_group), []).append(c)
    for v in buckets.values():
        v.sort(key=lambda c: (c.source_family.casefold(), c.carrier_id.casefold()))
    keys = sorted(buckets, key=lambda x: (x[0].casefold(), x[1].casefold()))
    out: list[E011Carrier] = []
    while len(out) < max_count:
        progressed = False
        for k in keys:
            if buckets[k] and len(out) < max_count:
                out.append(buckets[k].pop(0)); progressed = True
        if not progressed:
            break
    return out
