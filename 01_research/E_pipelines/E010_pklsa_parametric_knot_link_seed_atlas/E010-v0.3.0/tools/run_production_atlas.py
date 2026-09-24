from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import traceback
import zipfile
from pathlib import Path

from sst_pklsa.core import Workbench
from pklsa_builder.builder import build_topology_registry
from pklsa_builder.campaign import run_topology_campaign
from pklsa_builder.gilbert import iter_gilbert_record_headers
from pklsa_builder.models import QualificationConfig
from pklsa_builder.repo_finder import iter_file_records, scan_repository, write_scan_outputs
from pklsa_builder.source_discovery import topology_from_path


ALLOWED_GEOMETRY_ROLES = {
    "geometry",
    "source_geometry",
    "derived_geometry",
    "generated_geometry",
    "generated_control_geometry",
    "geometry_catalog",
}

_DB_IDENTITY_CACHE = {}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_within(path: Path, root: Path) -> bool:
    try:
        rp = path.resolve()
        rr = root.resolve()
        return rp == rr or rp.is_relative_to(rr)
    except Exception:
        return False


def known_contract_roots(workbench: Path, contract: dict, wb: Workbench) -> list[Path]:
    roots: list[Path] = []
    for spec in contract.get("sources", []):
        for rel in spec.get("canonical_paths", []):
            p = workbench / rel
            if p.exists():
                roots.append(p.resolve())
        for alias in spec.get("legacy_globs", []):
            p = workbench / alias
            if p.exists():
                roots.append(p.resolve())
    for src in wb.resolve_sources():
        if src.path:
            roots.append(Path(src.path).resolve())
    unique = []
    seen = set()
    for p in roots:
        s = str(p).lower()
        if s not in seen:
            seen.add(s)
            unique.append(p)
    return unique


def filter_unregistered(scan: dict, known_roots: list[Path]) -> tuple[list[dict], list[dict]]:
    known, unknown = [], []
    for rec in scan.get("unregistered_source_candidates", []):
        p = Path(rec["path"])
        if any(is_within(p, root) for root in known_roots):
            r = dict(rec)
            r["production_review"] = "REGISTERED_BY_SOURCE_CONTRACT"
            known.append(r)
        else:
            r = dict(rec)
            r["production_review"] = "BLOCKING_UNREGISTERED_SOURCE"
            unknown.append(r)
    return known, unknown


def natural_topology_key(label: str):
    # Knots first, then links. Within each group: crossing number, notation family, index.
    m = re.fullmatch(r"(\d+)([an])?_(\d+)", label, re.I)
    if m:
        fam = {None: 0, "a": 1, "n": 2}.get((m.group(2) or "").lower() or None, 3)
        return (0, int(m.group(1)), fam, int(m.group(3)), label)
    m = re.fullmatch(r"L(\d+)([an])?_?(\d+)", label, re.I)
    if m:
        fam = {None: 0, "a": 1, "n": 2}.get((m.group(2) or "").lower() or None, 3)
        return (1, int(m.group(1)), fam, int(m.group(3)), label)
    return (2, 10**9, 9, 10**9, label)


def discover_topology_ids(scan: dict) -> list[str]:
    topologies: set[str] = set()

    # Multi-record Gilbert catalogues carry topology IDs inside the catalogue, not filenames.
    for rec in iter_file_records(scan, catalog_id="A004", roles={"geometry_catalog"}):
        try:
            for gr in iter_gilbert_record_headers(rec["path"]):
                topo = gr.get("canonical_id")
                if topo:
                    topologies.add(str(topo))
        except Exception:
            # Qualification of this source will fail closed later if it is required for a topology.
            pass

    # File-native topologies from all geometry-bearing A001-A008 records.
    for rec in iter_file_records(scan, roles=ALLOWED_GEOMETRY_ROLES):
        cid = rec.get("catalog_id")
        if cid == "A004":
            continue
        topo = topology_from_path(rec["path"])
        if cid == "A008":
            topo = "3_1"  # E009/PTSA v1.0.0 is explicitly trefoil; hash fragments must never become topology IDs.
        if topo:
            topologies.add(str(topo))

    return sorted(topologies, key=natural_topology_key)


def normalize_db_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(label).lower())


def _identity_alias_index(registry_dir: Path, prefix: str) -> dict:
    alias_file = registry_dir / f"{prefix}_aliases.json"
    key = (str(alias_file.resolve()), alias_file.stat().st_mtime_ns if alias_file.exists() else None)
    cached = _DB_IDENTITY_CACHE.get(key)
    if cached is not None:
        return cached
    # Drop stale entries for the same file path after a registry rebuild.
    for old_key in list(_DB_IDENTITY_CACHE):
        if old_key[0] == str(alias_file.resolve()) and old_key != key:
            _DB_IDENTITY_CACHE.pop(old_key, None)
    if not alias_file.exists():
        return {}
    aliases = json.loads(alias_file.read_text(encoding="utf-8"))
    index = {}
    for alias, targets in aliases.items():
        n = normalize_db_label(alias)
        row = index.setdefault(n, {"aliases": set(), "targets": set()})
        row["aliases"].add(alias)
        row["targets"].update(str(x) for x in targets)
    _DB_IDENTITY_CACHE[key] = index
    return index


def topology_db_identity(registry_dir: Path, topology_id: str) -> dict:
    prefix = "linkinfo" if topology_id.upper().startswith("L") else "knotinfo"
    alias_file = registry_dir / f"{prefix}_aliases.json"
    if not alias_file.exists():
        return {"topology_id": topology_id, "database": prefix, "status": "DATABASE_ALIAS_FILE_MISSING", "pass": False}
    query_norm = normalize_db_label(topology_id)
    row = _identity_alias_index(registry_dir, prefix).get(query_norm)
    matches = sorted(row["aliases"]) if row else []
    canonical_targets = sorted(row["targets"]) if row else []
    return {
        "topology_id": topology_id,
        "database": prefix,
        "query_normalized": query_norm,
        "matched_aliases": matches,
        "canonical_targets": canonical_targets,
        "status": "MATCHED_UPSTREAM_DATABASE" if matches else "NO_UPSTREAM_DATABASE_MATCH",
        "pass": bool(matches),
    }


def admit_topology_ids(registry_dir: Path, raw_topologies: list[str]) -> tuple[list[str], list[dict], list[dict]]:
    """Split geometry-derived labels into canonical DB-mapped and audit-only labels.

    A source-local record, filename hash, or historical variant is not promoted into the
    publication topology namespace unless KnotInfo/LinkInfo establishes the identity.
    """
    admitted = []
    mapped = []
    unmapped = []
    for topo in raw_topologies:
        identity = topology_db_identity(registry_dir, topo)
        row = {"topology_id": topo, "identity": identity}
        if identity.get("pass"):
            admitted.append(topo)
            mapped.append(row)
        else:
            row["policy"] = "AUDIT_ONLY_NOT_ADMITTED"
            unmapped.append(row)
    return sorted(set(admitted), key=natural_topology_key), mapped, unmapped


def scientific_code_digest(package_root: Path) -> str:
    """Hash executable scientific code independently of the frozen release manifest.

    Drop-in research patches intentionally do not rewrite the original package manifest.
    The run context must nevertheless bind resume/reproducibility to the exact Python/C++
    implementation that produced the geometry ledger.
    """
    paths = []
    for rel in ("pklsa_builder", "sst_pklsa"):
        root = package_root / rel
        if root.exists():
            paths.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    for rel in ("cpp/pklsa_native.cpp", "setup.py", "pyproject.toml"):
        q = package_root / rel
        if q.exists():
            paths.append(q)
    h = hashlib.sha256()
    for q in sorted(set(paths), key=lambda x: str(x.relative_to(package_root)).replace("\\", "/")):
        rel = str(q.relative_to(package_root)).replace("\\", "/")
        h.update(rel.encode("utf-8")); h.update(b"\0")
        h.update(sha256_file(q).encode("ascii")); h.update(b"\n")
    return h.hexdigest()


def run_context(package_root: Path, workbench: Path, source_catalog: Path, contract: Path, poc_cfg: Path, full_cfg: Path) -> dict:
    manifest = package_root / "PACKAGE_MANIFEST.json"
    return {
        "schema": "E010-PKLSA-PRODUCTION-RUN-CONTEXT-1",
        "workbench_root": str(workbench.resolve()),
        "source_catalog": str(source_catalog.resolve()),
        "source_catalog_sha256": sha256_file(source_catalog),
        "source_contract": str(contract.resolve()),
        "source_contract_sha256": sha256_file(contract),
        "poc_config_sha256": sha256_file(poc_cfg),
        "full_config_sha256": sha256_file(full_cfg),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "scientific_code_sha256": scientific_code_digest(package_root),
        "package_manifest_sha256": sha256_file(manifest) if manifest.exists() else None,
    }


def compatible_context(old: dict, new: dict) -> bool:
    keys = [
        "workbench_root",
        "source_catalog_sha256",
        "source_contract_sha256",
        "poc_config_sha256",
        "full_config_sha256",
        "runner_sha256",
        "scientific_code_sha256",
        "package_manifest_sha256",
    ]
    return all(old.get(k) == new.get(k) for k in keys)


def compatible_scientific_context(old: dict, new: dict) -> bool:
    """Allow a runner-only patch to resume a preflight-only failed run.

    Scientific inputs must be byte-identical. This is deliberately stricter once any
    topology campaign output exists; then the exact runner hash remains part of the
    reproducibility boundary.
    """
    keys = [
        "workbench_root",
        "source_catalog_sha256",
        "source_contract_sha256",
        "poc_config_sha256",
        "full_config_sha256",
        "scientific_code_sha256",
        "package_manifest_sha256",
    ]
    return all(old.get(k) == new.get(k) for k in keys)


def has_scientific_campaign_output(output: Path) -> bool:
    # A source scan/preflight is not a scientific topology result. Any topology
    # campaign tree or campaign index is. Fail closed once those exist.
    return (
        (output / "CAMPAIGN_INDEX.json").exists()
        or (output / "poc" / "atlas").exists()
        or (output / "atlas").exists()
    )


def archive_tree(output: Path, archive_dir: Path) -> tuple[Path, str]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    zpath = archive_dir / f"{output.name}.zip"
    tmp = zpath.with_suffix(zpath.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for p in sorted(output.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(output.parent))
    tmp.replace(zpath)
    sha = sha256_file(zpath)
    zpath.with_suffix(zpath.suffix + ".sha256").write_text(f"{sha}  {zpath.name}\n", encoding="ascii")
    return zpath, sha


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fail-closed source-native E010 PKLSA production atlas runner")
    ap.add_argument("--workbench", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--contract", required=True)
    ap.add_argument("--source-catalog", required=True)
    ap.add_argument("--poc-config", required=True)
    ap.add_argument("--full-config", required=True)
    ap.add_argument("--archive-dir", required=True)
    ap.add_argument("--deep-hash", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)

    package_root = Path(__file__).resolve().parents[1]
    workbench = Path(args.workbench).resolve()
    output = Path(args.output).resolve()
    contract_path = Path(args.contract).resolve()
    source_catalog = Path(args.source_catalog).resolve()
    poc_cfg_path = Path(args.poc_config).resolve()
    full_cfg_path = Path(args.full_config).resolve()
    archive_dir = Path(args.archive_dir).resolve()

    output.mkdir(parents=True, exist_ok=True)
    preflight = output / "preflight"
    preflight.mkdir(parents=True, exist_ok=True)

    context = run_context(package_root, workbench, source_catalog, contract_path, poc_cfg_path, full_cfg_path)
    context_path = output / "RUN_CONTEXT.json"
    if context_path.exists():
        old = json.loads(context_path.read_text(encoding="utf-8"))
        if not args.resume:
            raise RuntimeError(f"output already contains RUN_CONTEXT.json: {output}; use --resume or choose a clean output directory")
        if not compatible_context(old, context):
            if compatible_scientific_context(old, context) and not has_scientific_campaign_output(output):
                write_json(preflight / "RUN_CONTEXT_UPGRADE.json", {
                    "status": "PREFLIGHT_ONLY_RUNNER_PATCH_ACCEPTED",
                    "reason": "scientific inputs are byte-identical and no topology campaign output exists",
                    "old_context": old,
                    "new_context": context,
                })
                write_json(context_path, context)
            else:
                raise RuntimeError("existing output was produced with a different Workbench/config/catalog/runner; refuse unsafe resume")
    else:
        write_json(context_path, context)

    # Gate 1: current repository-native source contract.
    wb = Workbench.open(workbench, contract_path)
    doctor = wb.doctor()
    write_json(preflight / "WORKBENCH_DOCTOR.json", doctor)
    if not doctor["coverage"]["pass"]:
        missing = [x["source_id"] for x in doctor["sources"] if x["required"] and not x["path"]]
        raise RuntimeError(f"required Workbench sources are missing: {missing}")

    # Gate 2: A001-A008 semantic adapter used by the current qualification core.
    print("[scan] repository source inventory" + (" + SHA-256" if args.deep_hash else ""), flush=True)
    scan = scan_repository(workbench, source_catalog, hash_files=args.deep_hash, search_depth=10, find_unregistered=True)
    write_scan_outputs(scan, output / "source_discovery")
    if not scan["coverage_gate"]["pass"]:
        raise RuntimeError("A001-A008 production source coverage gate failed; inspect source_discovery/A001_A008_COVERAGE.csv")

    # Old builder unregistered detection predates source_contract_v1. Filter it against
    # every source explicitly registered by the current contract before deciding to block.
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    known_roots = known_contract_roots(workbench, contract, wb)
    known_extra, unknown_extra = filter_unregistered(scan, known_roots)
    write_json(output / "source_discovery" / "UNREGISTERED_REGISTERED_BY_CONTRACT.json", known_extra)

    # IMPORTANT: repo_finder's unregistered search is intentionally heuristic and
    # directory-based. It can match mirrors, archived research products and consumers
    # merely because their paths contain tokens such as knotplot/katlas/ptsa/qhp.
    # Those candidates are NOT admitted by discover_from_repo_scan(): only the explicit
    # A001-A008 resolved roots enter qualification. Therefore unknown heuristic hits are
    # audit-only, not a publication blocker. This matches the source-contract policy:
    # unknown sources remain audit-only until explicitly registered.
    write_json(output / "source_discovery" / "UNREGISTERED_AUDIT_ONLY.json", unknown_extra)
    write_json(output / "source_discovery" / "UNREGISTERED_BLOCKING.json", [])
    unregistered_scan_count = len(scan.get("unregistered_source_candidates", []))
    unregistered_limit_reached = unregistered_scan_count >= 500
    unregistered_policy = {
        "schema": "E010-PKLSA-UNREGISTERED-SOURCE-POLICY-2",
        "policy": "AUDIT_ONLY_NOT_ADMITTED",
        "scanner_candidates_returned": unregistered_scan_count,
        "scanner_result_limit_maybe_reached": unregistered_limit_reached,
        "registered_by_contract_count": len(known_extra),
        "audit_only_unregistered_count": len(unknown_extra),
        "blocking_count": 0,
        "admission_boundary": "Only files discovered under explicit A001-A008 resolved roots are eligible for qualification; heuristic unregistered candidates are excluded.",
        "claim_boundary": "Publication-ready refers to the registered source contract, not to every source-looking directory anywhere in SST-Workbench.",
    }
    write_json(preflight / "UNREGISTERED_SOURCE_POLICY.json", unregistered_policy)
    if unknown_extra:
        suffix = " (scanner cap may have been reached)" if unregistered_limit_reached else ""
        print(f"[audit] {len(unknown_extra)} heuristic unregistered candidate(s) excluded from admission{suffix}; continuing", flush=True)

    # Gate 3: topology identity databases. These are bundled upstream snapshots and are
    # kept separate from geometry qualification.
    registry_dir = output / "topology_registry"
    knotinfo = package_root / "data" / "topology_sources" / "knotinfo_data_complete.xls.zip"
    linkinfo = package_root / "data" / "topology_sources" / "linkinfo_data_complete.xls"
    aliases, db_summary = build_topology_registry(knotinfo, linkinfo, registry_dir)
    write_json(preflight / "TOPOLOGY_DATABASE_GATE.json", db_summary)
    db_gate = bool(db_summary) and all(v.get("status") == "INGESTED" for v in db_summary.values())
    if not db_gate:
        raise RuntimeError("KnotInfo/LinkInfo database ingestion failed")

    # Discover raw labels from admitted geometry, then require an explicit upstream
    # KnotInfo/LinkInfo identity before a label enters the canonical production atlas.
    # This prevents source-local variants, hashes and malformed filenames from becoming
    # publication topology IDs while preserving them in an auditable ledger.
    raw_topologies = discover_topology_ids(scan)
    topologies, mapped_topologies, unmapped_topologies = admit_topology_ids(registry_dir, raw_topologies)
    write_json(preflight / "TOPOLOGY_IDENTITY_ADMISSION.json", {
        "schema": "E010-PKLSA-TOPOLOGY-IDENTITY-ADMISSION-1",
        "raw_candidate_count": len(raw_topologies),
        "admitted_count": len(topologies),
        "unmapped_audit_only_count": len(unmapped_topologies),
        "policy": "UPSTREAM_DATABASE_MATCH_REQUIRED_FOR_CANONICAL_ADMISSION",
        "mapped": mapped_topologies,
        "unmapped_audit_only": unmapped_topologies,
    })
    write_json(preflight / "TOPOLOGY_UNMAPPED_AUDIT_ONLY.json", unmapped_topologies)
    if "3_1" not in topologies:
        raise RuntimeError("trefoil 3_1 not found as a DB-mapped admitted source geometry")
    (output / "TOPOLOGIES.txt").write_text("\n".join(topologies) + "\n", encoding="utf-8")
    write_json(preflight / "TOPOLOGY_SET.json", {
        "raw_candidate_count": len(raw_topologies),
        "count": len(topologies),
        "unmapped_audit_only_count": len(unmapped_topologies),
        "topologies": topologies,
    })
    if unmapped_topologies:
        print(f"[audit] {len(unmapped_topologies)} source-local topology label(s) have no upstream DB identity and are excluded from canonical admission", flush=True)

    # Gate 4: trefoil proof-of-concept. This is deliberately cheaper than the final
    # publication ladder but exercises the exact same live source scan and DB registry.
    poc_cfg = QualificationConfig.load(poc_cfg_path)
    print("[poc] topology 3_1", flush=True)
    poc_summary = run_topology_campaign(
        "3_1",
        output / "poc" / "atlas",
        poc_cfg,
        workbench_root=workbench,
        base_root=None,
        alias_maps=aliases,
        registry_dir=registry_dir,
        repo_scan=scan,
    )
    poc_identity = topology_db_identity(registry_dir, "3_1")
    write_json(output / "poc" / "IDENTITY_DATABASE_GATE.json", poc_identity)
    if not poc_summary.get("qualification_gate_pass") or not poc_identity["pass"]:
        raise RuntimeError("trefoil POC failed; full atlas was not started")

    # Gate 5: full publication ladder. Results are checkpointed topology-by-topology,
    # so an interrupted long run can safely resume only under an identical RUN_CONTEXT.
    full_cfg = QualificationConfig.load(full_cfg_path)
    completed: list[dict] = []
    failed: list[dict] = []
    identity_rows: list[dict] = []

    for idx, topo in enumerate(topologies, 1):
        summary_path = output / "atlas" / topo / "qualification" / "summary.json"
        gate_path = output / "atlas" / topo / "qualification" / "PRODUCTION_GATE.json"
        summary = None
        if args.resume and summary_path.exists() and gate_path.exists():
            try:
                old_gate = json.loads(gate_path.read_text(encoding="utf-8"))
                if old_gate.get("pass") is True:
                    summary = json.loads(summary_path.read_text(encoding="utf-8"))
                    print(f"[{idx:03d}/{len(topologies):03d}] {topo}: resume PASS", flush=True)
            except Exception:
                summary = None

        if summary is None:
            print(f"[{idx:03d}/{len(topologies):03d}] {topo}: qualification", flush=True)
            try:
                summary = run_topology_campaign(
                    topo,
                    output / "atlas",
                    full_cfg,
                    workbench_root=workbench,
                    base_root=None,
                    alias_maps=aliases,
                    registry_dir=registry_dir,
                    repo_scan=scan,
                )
            except Exception as exc:
                err = {
                    "topology_id": topo,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                failed.append(err)
                write_json(output / "atlas" / topo / "qualification" / "PRODUCTION_EXCEPTION.json", err)
                continue

        identity = topology_db_identity(registry_dir, topo)
        identity_rows.append(identity)
        gate = {
            "topology_id": topo,
            "geometry_qualification_pass": bool(summary.get("qualification_gate_pass")),
            "identity_database_pass": bool(identity["pass"]),
            "pass": bool(summary.get("qualification_gate_pass") and identity["pass"]),
        }
        write_json(gate_path, gate)
        write_json(output / "atlas" / topo / "topology" / "PRODUCTION_IDENTITY_DATABASE.json", identity)
        if gate["pass"]:
            completed.append({"topology_id": topo, "summary": summary, "identity": identity})
        else:
            failed.append({"topology_id": topo, "summary": summary, "identity": identity})

    write_json(output / "IDENTITY_DATABASE_LEDGER.json", identity_rows)
    write_json(output / "FAILED_TOPOLOGIES.json", failed)
    write_json(output / "CAMPAIGN_INDEX.json", {
        "topology_count": len(topologies),
        "passed_count": len(completed),
        "failed_count": len(failed),
        "passed": [x["topology_id"] for x in completed],
        "failed": [x.get("topology_id") for x in failed],
    })

    # Source gate is about explicit registered-source coverage. Heuristic unregistered
    # candidates are excluded from admission and therefore do not invalidate this gate.
    source_gate = bool(scan["coverage_gate"]["pass"] and doctor["coverage"]["pass"])
    campaign_gate = len(failed) == 0 and len(completed) == len(topologies) and len(topologies) > 0
    identity_gate = len(identity_rows) == len(topologies) and all(x.get("pass") for x in identity_rows)
    release = {
        "schema": "E010-PKLSA-PRODUCTION-KNOT-LINK-BASIS-1",
        "e010_version": "0.3.0",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "workbench_root": str(workbench),
        "source_native_mode": True,
        "historical_v0_1_1_npz_required": False,
        "historical_v0_2_0_base_required": False,
        "raw_topology_candidate_count": len(raw_topologies),
        "topology_count": len(topologies),
        "unmapped_topology_candidate_count": len(unmapped_topologies),
        "unmapped_topology_policy": "AUDIT_ONLY_NOT_ADMITTED",
        "canonical_identity_admission_gate_pass": all(x["identity"].get("pass") for x in mapped_topologies) and len(topologies) > 0,
        "source_contract_gate_pass": bool(doctor["coverage"]["pass"]),
        "a001_a008_coverage_gate_pass": bool(scan["coverage_gate"]["pass"]),
        "unregistered_source_gate_pass": True,
        "unregistered_source_policy": "AUDIT_ONLY_NOT_ADMITTED",
        "unregistered_source_candidates_returned": unregistered_scan_count,
        "unregistered_source_candidates_audit_only": len(unknown_extra),
        "unregistered_scanner_result_limit_maybe_reached": unregistered_limit_reached,
        "topology_database_ingest_gate_pass": db_gate,
        "trefoil_poc_gate_pass": bool(poc_summary.get("qualification_gate_pass") and poc_identity["pass"]),
        "full_campaign_gate_pass": campaign_gate,
        "identity_database_gate_pass": identity_gate,
        "publication_ready_geometry_layer": bool(source_gate and db_gate and campaign_gate and identity_gate and len(topologies) > 0),
        "failed_topology_count": len(failed),
        "scientific_boundary": "Geometry/source/topology qualification only. This does not establish Euler/Biot-Savart dynamical stability or an SST particle claim.",
    }
    write_json(output / "RELEASE.json", release)

    if not release["publication_ready_geometry_layer"]:
        print(json.dumps(release, indent=2), flush=True)
        raise RuntimeError("full production gate failed; RELEASE.json is not publication-ready")

    zpath, zsha = archive_tree(output, archive_dir)
    result = dict(release)
    result["archive"] = str(zpath)
    result["archive_sha256"] = zsha
    # Keep RELEASE.json byte-stable with the copy inside the ZIP; archive identity is
    # carried by the external .sha256 sidecar and the terminal result below.
    print(json.dumps(result, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
