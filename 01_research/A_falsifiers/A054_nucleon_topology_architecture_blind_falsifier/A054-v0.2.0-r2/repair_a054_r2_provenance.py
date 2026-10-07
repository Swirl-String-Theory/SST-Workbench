from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPAIR_ID = "A054-v0.2.0-r2-provenance-repair-1"
IMMUTABLE = {
    "results_sha256": "CERT_RESULTS_BLIND.json",
    "analysis_sha256": "CERT_ANALYSIS_BLIND.json",
    "report_sha256": "CERT_REPORT_BLIND.md",
    "config_sha256": "CERT_CONFIG.json",
    "backend_qualification_sha256": "BACKEND_QUALIFICATION.json",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj, *, sort_keys=False) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8")


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def first_seen_result_ids(results: dict) -> list[str]:
    out, seen = [], set()
    for row in results.get("results", []):
        aid = row.get("anonymous_id")
        if aid and aid not in seen:
            seen.add(aid)
            out.append(aid)
    return out


def verify_result_completeness(results: dict, cfg: dict, expected_candidates: int) -> dict:
    sectors = list(cfg["circulation_sectors"])
    ladder = sorted(int(x) for x in cfg["n_ladder"])
    ids = first_seen_result_ids(results)
    if len(ids) != expected_candidates:
        fail(f"expected {expected_candidates} result candidates, found {len(ids)}")

    by = collections.defaultdict(list)
    for row in results.get("results", []):
        by[(row.get("anonymous_id"), row.get("sector"))].append(row)

    missing = []
    for aid in ids:
        for sec in sectors:
            rows = by.get((aid, sec), [])
            ns = [r.get("N") for r in rows]
            for n in ladder:
                if ns.count(n) != 1:
                    missing.append({"anonymous_id": aid, "sector": sec, "N": n, "count": ns.count(n)})
            if ns.count("SUMMARY") != 1:
                missing.append({"anonymous_id": aid, "sector": sec, "N": "SUMMARY", "count": ns.count("SUMMARY")})
    if missing:
        fail(f"result grid incomplete/duplicated; first problems: {missing[:10]}")

    numeric = sum(isinstance(r.get("N"), int) for r in results["results"])
    summaries = sum(r.get("N") == "SUMMARY" for r in results["results"])
    expected_numeric = expected_candidates * len(sectors) * len(ladder)
    expected_summaries = expected_candidates * len(sectors)
    if numeric != expected_numeric or summaries != expected_summaries:
        fail(
            f"result row count mismatch numeric={numeric}/{expected_numeric}, "
            f"summary={summaries}/{expected_summaries}"
        )
    return {
        "candidate_count": len(ids),
        "sectors": sectors,
        "n_ladder": ladder,
        "numeric_rows": numeric,
        "summary_rows": summaries,
        "total_rows": len(results["results"]),
    }


def repair_campaign(campaign: Path, *, force=False) -> dict:
    campaign = campaign.resolve()
    required = [
        "BLIND_MANIFEST.json",
        "CERT_RESULTS_BLIND.json",
        "CERT_ANALYSIS_BLIND.json",
        "CERT_REPORT_BLIND.md",
        "CERT_CONFIG.json",
        "BACKEND_QUALIFICATION.json",
        "CERT_BLIND_SEAL.json",
        "_private/PRIVATE_MAPPING.json",
    ]
    for rel in required:
        if not (campaign / rel).is_file():
            fail(f"missing required file: {rel}")

    original_seal_path = campaign / "CERT_BLIND_SEAL.json"
    original_manifest_path = campaign / "BLIND_MANIFEST.json"
    original_private_path = campaign / "_private" / "PRIVATE_MAPPING.json"
    original_seal = json.loads(original_seal_path.read_text(encoding="utf-8"))
    manifest = json.loads(original_manifest_path.read_text(encoding="utf-8"))
    private = json.loads(original_private_path.read_text(encoding="utf-8"))
    results = json.loads((campaign / "CERT_RESULTS_BLIND.json").read_text(encoding="utf-8"))
    cfg = json.loads((campaign / "CERT_CONFIG.json").read_text(encoding="utf-8"))

    # The actual scientific outputs must still be byte-identical to the historical seal.
    immutable_checks = {}
    for seal_key, rel in IMMUTABLE.items():
        got = sha256_file(campaign / rel)
        exp = original_seal.get(seal_key)
        immutable_checks[rel] = {"expected": exp, "actual": got, "pass": got == exp}
        if got != exp:
            fail(f"immutable scientific output no longer matches original seal: {rel}")

    expected_count = int(manifest.get("candidate_count", 0))
    if expected_count <= 0:
        fail("current manifest has no positive candidate_count")
    completeness = verify_result_completeness(results, cfg, expected_count)
    result_ids = first_seen_result_ids(results)

    current_candidates = manifest.get("candidates", [])
    current_private_map = private.get("mapping", {})
    current_ids = [c.get("anonymous_id") for c in current_candidates]
    if len(current_candidates) != expected_count or len(set(current_ids)) != expected_count:
        fail("current manifest candidate IDs are not a unique complete set")
    if set(current_ids) != set(current_private_map):
        fail("current manifest and current private mapping do not describe the same candidate-ID set")

    overlap = sorted(set(result_ids) & set(current_ids))
    if overlap and not force:
        fail(
            "result IDs overlap the current manifest; this repair is intended for the known mixed-campaign state. "
            "Use --force only after manual audit."
        )

    # Exact-byte blind-input SHA is the repair key. No geometric fuzzy matching is used.
    sha_to_candidates = collections.defaultdict(list)
    for c in current_candidates:
        sha_to_candidates[c.get("sha256")].append(c)
    duplicates = {h: xs for h, xs in sha_to_candidates.items() if h and len(xs) != 1}
    if duplicates:
        fail(f"current manifest contains non-unique blind-input SHA-256 values: {len(duplicates)}")

    bijection = []
    repaired_candidates = []
    repaired_mapping = {}
    used_current = set()
    for old_id in result_ids:
        old_file = campaign / "blind_inputs" / f"{old_id}.npz"
        if not old_file.is_file():
            fail(f"result candidate has no preserved blind input: {old_file.name}")
        input_sha = sha256_file(old_file)
        matches = sha_to_candidates.get(input_sha, [])
        if len(matches) != 1:
            fail(f"old candidate {old_id} has {len(matches)} exact-SHA matches in current manifest")
        cur = matches[0]
        cur_id = cur["anonymous_id"]
        if cur_id in used_current:
            fail(f"bijection collision: current candidate {cur_id} matched more than once")
        used_current.add(cur_id)

        sem = current_private_map.get(cur_id)
        if sem is None:
            fail(f"missing private semantics for matched current ID {cur_id}")
        if sem.get("geometry_sha256") and cur.get("geometry_sha256") and sem["geometry_sha256"] != cur["geometry_sha256"]:
            fail(f"geometry SHA mismatch between current manifest/private mapping for {cur_id}")

        rc = dict(cur)
        rc["anonymous_id"] = old_id
        rc["file"] = f"{old_id}.npz"
        rc["sha256"] = input_sha
        repaired_candidates.append(rc)

        rs = dict(sem)
        rs["provenance_repair_source_anonymous_id"] = cur_id
        repaired_mapping[old_id] = rs

        bijection.append({
            "result_anonymous_id": old_id,
            "source_mapping_anonymous_id": cur_id,
            "blind_input_sha256": input_sha,
            "geometry_sha256": cur.get("geometry_sha256"),
        })

    if len(used_current) != expected_count:
        fail(f"bijection did not consume all current candidates: {len(used_current)}/{expected_count}")

    # Backup the mixed state before modifying anything.
    backup = campaign / "_provenance_repair_backup"
    if backup.exists() and any(backup.iterdir()) and not force:
        fail(f"backup directory already exists and is non-empty: {backup}; refusing second repair without --force")
    backup.mkdir(parents=True, exist_ok=True)
    for src, name in [
        (original_manifest_path, "BLIND_MANIFEST.mixed_state.json"),
        (original_private_path, "PRIVATE_MAPPING.mixed_state.json"),
        (original_seal_path, "CERT_BLIND_SEAL.original.json"),
    ]:
        shutil.copy2(src, backup / name)

    # Rebuild the private mapping for the IDs actually used by CERT_RESULTS_BLIND.
    repaired_private = {
        "schema": "A054-CERT-PRIVATE-MAPPING-2.0-REPAIRED",
        "repair_id": REPAIR_ID,
        "salt": None,
        "salt_status": "ORIGINAL_RANDOM_SALT_NOT_RECOVERABLE; semantics recovered by exact blind-input SHA-256 bijection",
        "mapping": repaired_mapping,
        "preset": private.get("preset", manifest.get("preset")),
    }
    write_json(original_private_path, repaired_private)
    repaired_private_sha = sha256_file(original_private_path)

    repaired_manifest = dict(manifest)
    repaired_manifest["candidates"] = repaired_candidates
    repaired_manifest["candidate_count"] = len(repaired_candidates)
    repaired_manifest["private_mapping_sha256"] = repaired_private_sha
    repaired_manifest["provenance_repair"] = {
        "repair_id": REPAIR_ID,
        "reason": "mixed anonymous-ID preparation state after completed numerical certification",
        "method": "72/72 exact blind-input SHA-256 bijection; no scientific outputs recomputed",
        "original_seal_sha256": sha256_file(backup / "CERT_BLIND_SEAL.original.json"),
        "original_manifest_expected_sha256": original_seal.get("manifest_sha256"),
        "original_private_mapping_expected_sha256": original_seal.get("private_mapping_commitment"),
    }
    write_json(original_manifest_path, repaired_manifest)
    repaired_manifest_sha = sha256_file(original_manifest_path)

    # Blind-safe evidence: it links two anonymous namespaces but contains no architecture/knot labels.
    repair_bijection_path = campaign / "PROVENANCE_REPAIR_BIJECTION_BLIND.json"
    write_json(repair_bijection_path, {
        "schema": "A054-PROVENANCE-REPAIR-BIJECTION-1.0",
        "repair_id": REPAIR_ID,
        "method": "exact file SHA-256",
        "candidate_count": len(bijection),
        "bijection": bijection,
    })

    repair_report = {
        "schema": "A054-PROVENANCE-REPAIR-REPORT-1.0",
        "repair_id": REPAIR_ID,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "campaign": str(campaign),
        "scientific_outputs_recomputed": False,
        "scientific_outputs_modified": False,
        "immutable_original_seal_checks": immutable_checks,
        "result_grid": completeness,
        "mixed_state_before_repair": {
            "result_candidate_count": len(result_ids),
            "current_manifest_candidate_count": len(current_ids),
            "anonymous_id_overlap": len(overlap),
            "preserved_blind_input_npz_count": len(list((campaign / "blind_inputs").glob("*.npz"))),
            "original_manifest_actual_sha256": sha256_file(backup / "BLIND_MANIFEST.mixed_state.json"),
            "original_manifest_expected_sha256": original_seal.get("manifest_sha256"),
            "original_private_mapping_actual_sha256": sha256_file(backup / "PRIVATE_MAPPING.mixed_state.json"),
            "original_private_mapping_expected_sha256": original_seal.get("private_mapping_commitment"),
        },
        "repair_evidence": {
            "bijection_count": len(bijection),
            "bijection_unique": len({x["source_mapping_anonymous_id"] for x in bijection}) == len(bijection),
            "matching_key": "blind input file SHA-256 (exact bytes)",
            "bijection_file": repair_bijection_path.name,
            "bijection_sha256": sha256_file(repair_bijection_path),
        },
        "repaired_state": {
            "manifest_sha256": repaired_manifest_sha,
            "private_mapping_sha256": repaired_private_sha,
        },
        "interpretation": (
            "This repair restores namespace/provenance consistency only. It does not change any computed "
            "dynamics, gates, analysis, report, configuration, or backend qualification. The historical "
            "pre-repair seal is retained in _provenance_repair_backup for audit."
        ),
    }
    repair_report_path = campaign / "PROVENANCE_REPAIR_REPORT.json"
    write_json(repair_report_path, repair_report)

    repaired_seal = {
        "schema": "A054-CERT-BLIND-SEAL-2.0-REPAIRED",
        "repair_id": REPAIR_ID,
        "manifest_sha256": repaired_manifest_sha,
        "results_sha256": sha256_file(campaign / "CERT_RESULTS_BLIND.json"),
        "analysis_sha256": sha256_file(campaign / "CERT_ANALYSIS_BLIND.json"),
        "report_sha256": sha256_file(campaign / "CERT_REPORT_BLIND.md"),
        "config_sha256": sha256_file(campaign / "CERT_CONFIG.json"),
        "backend_qualification_sha256": sha256_file(campaign / "BACKEND_QUALIFICATION.json"),
        "private_mapping_commitment": repaired_private_sha,
        "original_seal_sha256": sha256_file(backup / "CERT_BLIND_SEAL.original.json"),
        "repair_report_sha256": sha256_file(repair_report_path),
        "bijection_sha256": sha256_file(repair_bijection_path),
        "scientific_outputs_recomputed": False,
    }
    write_json(original_seal_path, repaired_seal)

    # Final exact verification using the contract A055 v0.3.0 checks.
    final_checks = {
        "BLIND_MANIFEST.json": (repaired_seal["manifest_sha256"], sha256_file(original_manifest_path)),
        "CERT_RESULTS_BLIND.json": (repaired_seal["results_sha256"], sha256_file(campaign / "CERT_RESULTS_BLIND.json")),
        "CERT_ANALYSIS_BLIND.json": (repaired_seal["analysis_sha256"], sha256_file(campaign / "CERT_ANALYSIS_BLIND.json")),
        "CERT_REPORT_BLIND.md": (repaired_seal["report_sha256"], sha256_file(campaign / "CERT_REPORT_BLIND.md")),
        "CERT_CONFIG.json": (repaired_seal["config_sha256"], sha256_file(campaign / "CERT_CONFIG.json")),
        "BACKEND_QUALIFICATION.json": (repaired_seal["backend_qualification_sha256"], sha256_file(campaign / "BACKEND_QUALIFICATION.json")),
        "_private/PRIVATE_MAPPING.json": (repaired_seal["private_mapping_commitment"], sha256_file(original_private_path)),
    }
    bad = [name for name, (exp, got) in final_checks.items() if exp != got]
    if bad:
        fail(f"post-repair A055 seal verification failed: {bad}")

    # Verify manifest/result namespace consistency after repair.
    repaired_id_set = {c["anonymous_id"] for c in repaired_manifest["candidates"]}
    if repaired_id_set != set(result_ids) or repaired_id_set != set(repaired_mapping):
        fail("post-repair anonymous-ID namespaces are not identical")

    status = {
        "status": "PASS",
        "repair_id": REPAIR_ID,
        "campaign": str(campaign),
        "a055_seal_contract": "PASS",
        "candidate_namespace_consistency": "PASS",
        "exact_sha256_bijection": f"{len(bijection)}/{expected_count}",
        "numeric_cells_preserved": completeness["numeric_rows"],
        "summary_rows_preserved": completeness["summary_rows"],
        "scientific_outputs_recomputed": False,
        "new_seal_sha256": sha256_file(original_seal_path),
    }
    write_json(campaign / "PROVENANCE_REPAIR_STATUS.json", status)
    return status


def verify_only(campaign: Path) -> dict:
    campaign = campaign.resolve()
    seal = json.loads((campaign / "CERT_BLIND_SEAL.json").read_text(encoding="utf-8"))
    checks = {
        "manifest": (seal["manifest_sha256"], sha256_file(campaign / "BLIND_MANIFEST.json")),
        "results": (seal["results_sha256"], sha256_file(campaign / "CERT_RESULTS_BLIND.json")),
        "analysis": (seal["analysis_sha256"], sha256_file(campaign / "CERT_ANALYSIS_BLIND.json")),
        "report": (seal["report_sha256"], sha256_file(campaign / "CERT_REPORT_BLIND.md")),
        "config": (seal["config_sha256"], sha256_file(campaign / "CERT_CONFIG.json")),
        "backend": (seal["backend_qualification_sha256"], sha256_file(campaign / "BACKEND_QUALIFICATION.json")),
        "private_mapping": (seal["private_mapping_commitment"], sha256_file(campaign / "_private" / "PRIVATE_MAPPING.json")),
    }
    bad = {k: {"expected": a, "actual": b} for k, (a, b) in checks.items() if a != b}
    man = json.loads((campaign / "BLIND_MANIFEST.json").read_text(encoding="utf-8"))
    res = json.loads((campaign / "CERT_RESULTS_BLIND.json").read_text(encoding="utf-8"))
    priv = json.loads((campaign / "_private" / "PRIVATE_MAPPING.json").read_text(encoding="utf-8"))
    rid = set(first_seen_result_ids(res)); mid = {x["anonymous_id"] for x in man["candidates"]}; pid = set(priv["mapping"])
    return {
        "status": "PASS" if not bad and rid == mid == pid else "FAIL",
        "seal_mismatches": bad,
        "result_ids": len(rid), "manifest_ids": len(mid), "private_ids": len(pid),
        "namespace_equal": rid == mid == pid,
        "seal_schema": seal.get("schema"),
    }


def auto_find_campaign(root: Path) -> Path:
    root = root.resolve()
    out = root / "A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs"
    if not out.is_dir():
        fail(f"outputs directory not found: {out}")
    candidates = []
    for p in out.glob("full_*"):
        if (p / "CERT_RESULTS_BLIND.json").is_file() and (p / "CERT_BLIND_SEAL.json").is_file():
            candidates.append(p)
    if len(candidates) != 1:
        fail(f"expected exactly one completed full_* campaign, found {len(candidates)}: {[p.name for p in candidates]}")
    return candidates[0]


def main() -> None:
    ap = argparse.ArgumentParser(description="Repair A054 v0.2.0-r2 mixed anonymous-ID provenance without recomputing dynamics")
    ap.add_argument("campaign", nargs="?", help="path to full_<timestamp> campaign; omit when run from A054-v0.2.0-r2 root")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    campaign = Path(args.campaign) if args.campaign else auto_find_campaign(Path.cwd())
    result = verify_only(campaign) if args.verify_only else repair_campaign(campaign, force=args.force)
    print(json.dumps(result, indent=2))
    if result.get("status") != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
