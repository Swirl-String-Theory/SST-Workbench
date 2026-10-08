#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open("r", encoding="utf-8-sig") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception as e:
                raise RuntimeError(f"{path}:{n}: invalid JSON: {e}") from e
            if not isinstance(row, dict):
                raise RuntimeError(f"{path}:{n}: JSONL row must be an object")
            out.append(row)
    return out


def active_specs(topo_cfg: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    p = "FULL" if profile == "PLAN" else profile
    return [x for x in topo_cfg["topologies"] if p in x.get("profiles", [])]


def build_manifest(
    outputs: Path,
    cfg: dict[str, Any],
    topo_cfg: dict[str, Any],
    profile: str,
    destination: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    index_path = outputs / cfg["sklsa"]["static_index_file"]
    anchors_path = outputs / cfg["sklsa"]["provider_anchors_file"]
    index_rows = load_json(index_path)
    anchors = read_jsonl(anchors_path)

    if not isinstance(index_rows, list):
        raise RuntimeError("E011 STATIC_READY_INDEX.json must be a JSON list")

    index_by_topo = {str(x.get("topology_id")): x for x in index_rows if isinstance(x, dict)}
    anchors_by_topo: dict[str, list[dict[str, Any]]] = {}
    for row in anchors:
        tid = str(row.get("topology_id", ""))
        if row.get("static_ready") is True and row.get("provider_anchor") is True and tid:
            anchors_by_topo.setdefault(tid, []).append(row)

    count = cfg["provider_anchors_per_topology"]["FULL" if profile == "PLAN" else profile]
    selected = []
    availability = []
    missing_required = []

    for spec in active_specs(topo_cfg, profile):
        tid = spec["id"]
        idx = index_by_topo.get(tid)
        rows = anchors_by_topo.get(tid, [])

        status = idx.get("static_status") if idx else "NOT_PRESENT_IN_E011_STATIC_INDEX"
        static_ready = bool(idx and idx.get("static_ready") is True)

        if not static_ready or not rows:
            item = {
                "topology": tid,
                "class": spec.get("class"),
                "required": bool(spec.get("required")),
                "status": "NOT_AVAILABLE_STATIC_READY",
                "e011_static_status": status,
                "reasons": (idx or {}).get("static_not_ready_reasons", ["no STATIC_READY provider anchor"]),
                "available_provider_anchors": 0,
                "selected_provider_anchors": 0,
            }
            availability.append(item)
            if spec.get("required"):
                missing_required.append(item)
            continue

        # provider anchors are already selected by E011's target-free policy.
        rows = sorted(rows, key=lambda r: (
            str(r.get("provider_group", "")),
            str(r.get("static_seed_id", "")),
        ))
        chosen = rows[:count]

        availability.append({
            "topology": tid,
            "class": spec.get("class"),
            "required": bool(spec.get("required")),
            "status": "AVAILABLE",
            "e011_static_status": status,
            "available_provider_anchors": len(rows),
            "selected_provider_anchors": len(chosen),
            "provider_groups": [r.get("provider_group") for r in chosen],
        })

        for r in chosen:
            loc = r.get("source_locator") or {}
            selected.append({
                "topology_id": tid,
                "class": spec.get("class"),
                "roles": spec.get("roles", []),
                "static_seed_id": r.get("static_seed_id"),
                "carrier_id": r.get("carrier_id"),
                "provider_group": r.get("provider_group"),
                "lineage_group": r.get("lineage_group"),
                "evidence_class": r.get("evidence_class"),
                "e011_static_status": status,
                "finest_resolution": r.get("finest_resolution"),
                "capabilities": r.get("capabilities"),
                "source_locator": loc,
                "geometry_sha256": loc.get("geometry_sha256"),
                "raw_sha256": loc.get("raw_sha256"),
                "source_path": loc.get("source_path"),
                "representation": loc.get("representation"),
                "e011_provider_anchor_policy": r.get("provider_anchor_policy"),
            })

    if missing_required:
        raise RuntimeError(
            "Required E013 core topologies are not STATIC_READY in E011:\n" +
            json.dumps(missing_required, indent=2)
        )

    manifest = {
        "schema": "E013-COMMON-CARRIER-MANIFEST-1",
        "campaign_version": cfg["campaign_version"],
        "profile": profile,
        "source_authority": "E011 SKLSA STATIC_READY provider anchors",
        "sklsa_release_id": cfg["sklsa"]["release_id"],
        "sklsa_static_index_sha256": sha256_file(index_path),
        "sklsa_provider_anchors_sha256": sha256_file(anchors_path),
        "selected_carrier_count": len(selected),
        "topology_availability": availability,
        "carriers": selected,
        "legacy_falsifier_outputs_used_as_evidence": False,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["content_sha256_without_self_field"] = hashlib.sha256(canonical).hexdigest()
    dump_json(destination, manifest)
    return manifest, availability


def contract_check(c: dict[str, Any], cfg: dict[str, Any]) -> tuple[bool, str]:
    req = cfg["required_member_contract"]
    if c.get("enabled") is False:
        return False, "disabled"
    if c.get("schema") != req["schema"]:
        return False, "schema mismatch"
    if c.get("input_geometry_source") != req["input_geometry_source"]:
        return False, "not bound to E013 common SKLSA anchors"
    if c.get("forbid_legacy_outputs") is not True:
        return False, "legacy outputs not explicitly forbidden"
    if c.get("sklsa_required") is not True:
        return False, "sklsa_required is not true"
    accepted = c.get("accepted_sklsa_release_ids", [])
    if accepted and cfg["sklsa"]["release_id"] not in accepted:
        return False, f'{cfg["sklsa"]["release_id"]} not accepted'
    run = c.get("run")
    if not isinstance(run, dict) or not run.get("command"):
        return False, "missing run command"
    return True, "eligible"


def fmt(s: Any, mapping: dict[str, str]) -> str:
    return str(s).format(**mapping)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, choices=["PLAN","BASIC","FULL","CERTIFY"])
    ap.add_argument("--workbench-root", required=True)
    ap.add_argument("--campaign-config", required=True)
    ap.add_argument("--topology-manifest", required=True)
    a = ap.parse_args()

    wb = Path(a.workbench_root).resolve()
    cfg_path = Path(a.campaign_config).resolve()
    topo_path = Path(a.topology_manifest).resolve()
    cfg = load_json(cfg_path)
    topo_cfg = load_json(topo_path)

    sklsa_root = wb / cfg["sklsa"]["release_root_rel"]
    outputs = sklsa_root / cfg["sklsa"]["outputs_rel"]
    if not outputs.exists():
        print(f"[ERROR] E011 SKLSA outputs not found: {outputs}", file=sys.stderr)
        return 2

    required_paths = []
    for name in cfg["sklsa"]["required_files"]:
        p = outputs / name
        if not p.exists():
            print(f"[ERROR] Required E011 file missing: {p}", file=sys.stderr)
            return 2
        required_paths.append(p)

    run_summary = load_json(outputs / "RUN_SUMMARY.json")
    if run_summary.get("execution_gate") != "PASS":
        print("[ERROR] E011 execution_gate is not PASS.", file=sys.stderr)
        return 2
    if str(run_summary.get("e011_version")) != "0.3.0":
        print(f"[ERROR] Unexpected E011 version: {run_summary.get('e011_version')}", file=sys.stderr)
        return 2

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_id = f'{cfg["campaign_id_prefix"]}-{a.profile}-{stamp}'
    out_root = wb / cfg["output_root_rel"] / campaign_id
    out_root.mkdir(parents=True, exist_ok=False)

    dump_json(out_root / "CROSS_PROTOCOL_FREEZE.json", {
        "schema": "E013-CROSS-PROTOCOL-FREEZE-1",
        "campaign_id": campaign_id,
        "profile": a.profile,
        "campaign_version": cfg["campaign_version"],
        "campaign_config_sha256": sha256_file(cfg_path),
        "topology_manifest_sha256": sha256_file(topo_path),
        "sklsa_release_id": cfg["sklsa"]["release_id"],
        "sklsa_root": str(sklsa_root),
        "sklsa_required_files": [
            {"path": str(p), "sha256": sha256_file(p)} for p in required_paths
        ],
        "legacy_falsifier_outputs_used_as_evidence": False,
    })

    manifest_path = out_root / "CROSS_CARRIER_MANIFEST.json"
    try:
        manifest, availability = build_manifest(outputs, cfg, topo_cfg, a.profile, manifest_path)
    except Exception as e:
        dump_json(out_root / "CROSS_RUN_SUMMARY.json", {
            "schema": "E013-CROSS-RUN-SUMMARY-1",
            "campaign_id": campaign_id,
            "status": "INFRASTRUCTURE_FAIL",
            "error": str(e),
        })
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    print(f"[E013] Campaign         : {campaign_id}")
    print(f"[E013] SKLSA release    : {cfg['sklsa']['release_id']}")
    print(f"[E013] Selected anchors : {manifest['selected_carrier_count']}")
    print("[E013] Topology availability:")
    for x in availability:
        print(
            f"  {x['topology']:<5} {x['status']:<28} "
            f"E011={x.get('e011_static_status')} "
            f"selected={x.get('selected_provider_anchors',0)}"
        )

    contract_paths = sorted(wb.glob(cfg["member_contract_glob"]))
    eligible, rejected = [], []
    for p in contract_paths:
        try:
            c = load_json(p)
        except Exception as e:
            rejected.append({"path": str(p), "reason": f"invalid JSON: {e}", "contract": {}})
            continue
        ok, reason = contract_check(c, cfg)
        item = {"path": str(p), "reason": reason, "contract": c}
        (eligible if ok else rejected).append(item)

    eligible.sort(key=lambda x: (
        int(x["contract"].get("stage", 9999)),
        str(x["contract"].get("catalog_id", "")),
        str(x["contract"].get("version", "")),
    ))

    dump_json(out_root / "MEMBER_DISCOVERY.json", {
        "schema": "E013-MEMBER-DISCOVERY-1",
        "eligible": [
            {
                "path": x["path"],
                "catalog_id": x["contract"].get("catalog_id"),
                "version": x["contract"].get("version"),
                "stage": x["contract"].get("stage"),
                "description": x["contract"].get("description"),
            } for x in eligible
        ],
        "rejected": [
            {
                "path": x["path"],
                "catalog_id": x["contract"].get("catalog_id"),
                "version": x["contract"].get("version"),
                "reason": x["reason"],
            } for x in rejected
        ],
    })

    print(f"[E013] Eligible members : {len(eligible)}")
    print(f"[E013] Rejected members : {len(rejected)}")
    print(f"[E013] Output root      : {out_root}")

    if a.profile == "PLAN":
        status = "READY" if eligible else "READY_NO_MEMBERS"
        dump_json(out_root / "CROSS_RUN_SUMMARY.json", {
            "schema": "E013-CROSS-RUN-SUMMARY-1",
            "campaign_id": campaign_id,
            "profile": a.profile,
            "status": status,
            "selected_carrier_count": manifest["selected_carrier_count"],
            "eligible_member_count": len(eligible),
            "legacy_falsifier_outputs_used_as_evidence": False,
        })
        return 0

    if not eligible:
        print("[E013] No eligible member contracts yet; carrier freeze is valid.")
        print("       Status: READY_NO_MEMBERS")
        dump_json(out_root / "CROSS_RUN_SUMMARY.json", {
            "schema": "E013-CROSS-RUN-SUMMARY-1",
            "campaign_id": campaign_id,
            "profile": a.profile,
            "status": "READY_NO_MEMBERS",
            "selected_carrier_count": manifest["selected_carrier_count"],
            "eligible_member_count": 0,
            "legacy_falsifier_outputs_used_as_evidence": False,
        })
        return 0

    env_base = os.environ.copy()
    env_base["SST_CROSS_FALSIFIER"] = "1"
    env_base["SST_DISABLE_LEGACY_RESULTS"] = "1"
    env_base["SST_CROSS_REQUIRE_SKLSA"] = "1"
    env_base["SST_CROSS_CAMPAIGN_ID"] = campaign_id
    env_base["SST_CROSS_CARRIER_MANIFEST"] = str(manifest_path)
    env_base["SST_SKLSA_RELEASE_ROOT"] = str(sklsa_root)
    env_base["SST_CROSS_OUTPUT_ROOT"] = str(out_root / "members")
    env_base.setdefault("SST_NATIVE_THREADS", str(cfg["runtime"]["native_threads_default"]))

    results = []
    runtime_errors = 0
    for item in eligible:
        c = item["contract"]
        cp = Path(item["path"])
        member_root = cp.parent
        run = c["run"]
        mapping = {
            "profile": a.profile,
            "workbench_root": str(wb),
            "campaign_id": campaign_id,
            "carrier_manifest": str(manifest_path),
            "cross_output_root": str(out_root / "members"),
            "sklsa_release_root": str(sklsa_root),
        }
        wd = (member_root / fmt(run.get("working_directory", "."), mapping)).resolve()
        command = fmt(run["command"], mapping)
        args = [fmt(x, mapping) for x in run.get("args", [])]

        log_dir = out_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        safe = f'{c.get("catalog_id","UNKNOWN")}_{c.get("version","UNKNOWN")}'.replace(os.sep, "_")
        log_path = log_dir / f"{safe}.log"

        if not wd.exists():
            rc = -1
            status = "RUNTIME_ERROR"
            reason = f"working directory missing: {wd}"
        else:
            if os.name == "nt" and command.lower().endswith((".cmd",".bat")):
                argv = ["cmd.exe","/d","/s","/c","call",command,*args]
            else:
                argv = [command,*args]
            print(f"[E013] RUN stage={c.get('stage')} {c.get('catalog_id')} {c.get('version')}")
            with log_path.open("w", encoding="utf-8", errors="replace") as log:
                log.write(f"# E013 child run\n# argv={argv!r}\n# cwd={str(wd)!r}\n\n")
                proc = subprocess.run(
                    argv, cwd=wd, env=env_base,
                    stdout=log, stderr=subprocess.STDOUT,
                    text=True, shell=False
                )
            rc = proc.returncode
            status = "COMPLETED" if rc == 0 else "RUNTIME_ERROR"
            reason = None

        if rc != 0:
            runtime_errors += 1
        results.append({
            "catalog_id": c.get("catalog_id"),
            "version": c.get("version"),
            "stage": c.get("stage"),
            "status": status,
            "returncode": rc,
            "reason": reason,
            "contract_path": str(cp),
            "log_path": str(log_path),
        })
        if rc != 0 and not cfg["runtime"].get("continue_after_child_runtime_error", True):
            break

    dump_json(out_root / "CROSS_RUN_SUMMARY.json", {
        "schema": "E013-CROSS-RUN-SUMMARY-1",
        "campaign_id": campaign_id,
        "profile": a.profile,
        "status": "COMPLETED_WITH_RUNTIME_ERRORS" if runtime_errors else "COMPLETED",
        "selected_carrier_count": manifest["selected_carrier_count"],
        "member_results": results,
        "runtime_error_count": runtime_errors,
        "legacy_falsifier_outputs_used_as_evidence": False,
        "note": "Child return code is execution status; scientific gate states remain in fresh child outputs.",
    })
    return 1 if runtime_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
