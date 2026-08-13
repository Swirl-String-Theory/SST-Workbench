#!/usr/bin/env python3
"""Run the pre-registered blind H0-H5/topology campaign without SST target inputs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from blind_utils import (
    assert_no_reveal_environment,
    json_dump,
    json_load,
    sha256_file,
    validate_blind_config,
)
from sst_hopf_common import runtime_provenance

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--candidate-root", type=Path, default=Path("blind_inputs/candidates"))
    p.add_argument("--output", type=Path, default=Path("results/blind"))
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--force-build", action="store_true")
    return p.parse_args()


def run(cmd: list[str], env: dict[str, str], log: Path) -> dict:
    print("\n>>", " ".join(cmd), flush=True)
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    elapsed = time.perf_counter() - t0
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(proc.stdout, encoding="utf-8")
    print(proc.stdout, end="")
    return {"command": cmd, "returncode": proc.returncode, "elapsed_s": elapsed, "log": str(log)}


def find_gate(payload: dict, gate: str) -> dict | None:
    if payload.get("gate") == gate:
        return payload
    for item in payload.get("gates", []):
        if isinstance(item, dict) and item.get("gate") == gate:
            return item
    for value in payload.values():
        if isinstance(value, dict):
            found = find_gate(value, gate)
            if found:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = find_gate(item, gate)
                    if found:
                        return found
    return None


def remove_heavy_npz(root: Path) -> list[str]:
    removed = []
    for path in root.rglob("*.npz"):
        path.unlink()
        removed.append(str(path.relative_to(root)).replace("\\", "/"))
    return removed


def main() -> int:
    args = parse_args()
    assert_no_reveal_environment()
    cfg = json_load(args.config)
    validate_blind_config(cfg)

    if (ROOT / "sst_reveal.json").exists():
        raise RuntimeError(
            "sst_reveal.json already exists. Blind production runs require reveal targets to remain absent until after sealing."
        )

    if "private_reveal" in str(args.candidate_root).lower() or "private_reveal" in str(args.output).lower():
        raise RuntimeError("Blind runner refuses private_reveal paths")

    candidate_manifest = args.candidate_root.parent / "candidate_pack_manifest.json"
    if not candidate_manifest.exists():
        raise FileNotFoundError("No blind candidate pack. Run PREPARE_BLIND_CAMPAIGN.cmd first.")

    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "SEALED_MANIFEST.json").exists():
        raise RuntimeError("Blind result directory is already SEALED. Start a new campaign directory instead.")

    logs = out / "logs"
    core = out / "core"
    s02 = core / "step02_hopf_benchmark"
    s03 = core / "step03_toroflux"
    s04 = core / "step04_hopf_charge"
    s05 = core / "step05_identity_selftest"
    s07 = core / "step07_double_cover_selftest"
    sc = out / "candidates"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["SST_HOPF_FORCE_PYTHON"] = "1" if args.force_python else "0"
    env["SST_HOPF_FORCE_BUILD"] = "1" if args.force_build else "0"
    env["SST_HOPF_BUILD_VERBOSE"] = "0"

    records = []
    if not args.force_python:
        cmd = [sys.executable, "-m", "sst_hopf_native.build_ext_if_needed", "--strict", "--quiet"]
        if args.force_build:
            cmd.append("--force")
        rec = run(cmd, env, logs / "00_build.log")
        records.append({"step": "build", **rec})
        if rec["returncode"] != 0:
            json_dump(out / "blind_run_summary.json", {"ok": False, "records": records, "sst_inputs_used": False})
            return rec["returncode"]

    ncfg = cfg["numerics"]
    commands = [
        ("H0_H3", [
            sys.executable, "02_analytische_hopf_benchmark.py",
            "--output", str(s02),
            "--resolutions", *[str(v) for v in ncfg["hopf_resolutions"]],
            "--extent", str(ncfg["hopf_extent"]),
            "--fiber-samples", str(ncfg["fiber_samples"]),
            "--integer-tolerance", str(cfg["comparison_thresholds"]["standard_abs"]),
        ]),
        ("H4", [
            sys.executable, "03_toroflux_spinorveld.py",
            "--output", str(s03),
            "--n-grid", str(ncfg["toroflux_grid"]),
        ]),
        ("H1_H3_director", [
            sys.executable, "04_hopf_lading_numeriek.py",
            str(s02 / "analytic_hopf_benchmark.npz"),
            "--output", str(s04),
            "--director-order", str(ncfg["director_order"]),
        ]),
    ]
    if cfg["self_tests"].get("run_helicity_identity", False):
        commands.append(("H5_IDENTITY_SELF_TEST", [
            sys.executable, "05_heliciteitsbridge.py",
            str(s04 / "hopf_charge_fields.npz"),
            "--output", str(s05),
        ]))
    if cfg["self_tests"].get("run_su2_double_cover", False):
        commands.append(("H9_KINEMATIC_SELF_TEST", [
            sys.executable, "07_vier_pi_configuratieruimte.py",
            "--output", str(s07),
            "--samples", "4001",
        ]))
    commands.append(("ANONYMOUS_CANDIDATES", [
        sys.executable, "run_blind_candidates.py",
        "--config", str(args.config),
        "--candidate-root", str(args.candidate_root),
        "--output", str(sc),
    ]))

    ok = True
    for step, cmd in commands:
        rec = run(cmd, env, logs / f"{step}.log")
        records.append({"step": step, **rec})
        if rec["returncode"] != 0:
            ok = False
            break

    if not ok:
        json_dump(out / "blind_run_summary.json", {
            "campaign_id": cfg["campaign_id"],
            "blind": True,
            "sst_inputs_used": False,
            "ok": False,
            "records": records,
        })
        return 2

    ev02 = json_load(s02 / "H0_H3_evidence.json")
    ev04 = json_load(s04 / "H1_H3_evidence.json")
    ev03 = json_load(s03 / "H4_toroflux_evidence.json")
    h1_step2 = find_gate(ev02, "H1") or {}
    h2 = find_gate(ev02, "H2") or {}
    h3_step2 = find_gate(ev02, "H3") or {}
    h1_step4 = find_gate(ev04, "H1") or {}
    h3_step4 = find_gate(ev04, "H3") or {}

    self_tests = {}
    if (s05 / "H5_evidence.json").exists():
        h5 = json_load(s05 / "H5_evidence.json")
        self_tests["H5_identity"] = {
            "classification": h5.get("bridge_classification"),
            "status": h5.get("status"),
            "evidence_class": "PIPELINE_SELF_TEST_NOT_PHYSICAL_EVIDENCE",
            "residuals": h5.get("residuals", {}),
        }
    if (s07 / "H9_evidence.json").exists():
        h9 = json_load(s07 / "H9_evidence.json")
        self_tests["H9_double_cover"] = {
            "status": h9.get("status"),
            "evidence_class": "KINEMATIC_SELF_TEST_NOT_SST_CONFIGURATION_SPACE_EVIDENCE",
            "residuals": h9.get("residuals", {}),
        }

    observables = {
        "campaign_id": cfg["campaign_id"],
        "blind": True,
        "sst_inputs_used": False,
        "target_values_used": False,
        "candidate_identity_read": False,
        "runtime": runtime_provenance(),
        "pre_registered_thresholds": cfg["comparison_thresholds"],
        "blind_evidence": {
            "H0_H4": {
                "H1_spinor": {
                    "q_hopf": h1_step2.get("residuals", {}).get("q_hopf"),
                    "delta_integer": h1_step2.get("residuals", {}).get("delta_integer"),
                    "qualification": h1_step2.get("qualification"),
                },
                "H1_director": {
                    "q_hopf": h1_step4.get("residuals", {}).get("q_director_projected"),
                    "delta_integer": h1_step4.get("residuals", {}).get("delta_integer_director"),
                    "delta_routes": h1_step4.get("residuals", {}).get("delta_routes"),
                    "delta_longitudinal": h1_step4.get("residuals", {}).get("delta_longitudinal"),
                    "qualification": h1_step4.get("qualification"),
                    "director_reconstruction_qualification": h1_step4.get("director_reconstruction_qualification"),
                },
                "H2_gauge": {
                    "status": h2.get("status"),
                    "delta_gauge": h2.get("residuals", {}).get("delta_gauge"),
                },
                "H3_preimage": {
                    "linking_number": h3_step2.get("residuals", {}).get("linking_number"),
                    "delta_link_integer": h3_step2.get("residuals", {}).get("delta_link"),
                    "step4_delta_link_spinor": h3_step4.get("residuals", {}).get("delta_link_spinor"),
                    "step4_delta_link_director": h3_step4.get("residuals", {}).get("delta_link_director"),
                    "qualification": h3_step4.get("qualification"),
                },
                "H4_toroflux": {
                    "status": ev03.get("status"),
                    "residuals": ev03.get("residuals", {}),
                },
            }
        },
        "self_tests_excluded_from_blind_physical_evidence": self_tests,
        "not_run_blind": {
            "H6": "requires an independently reduced physical action",
            "H7": "conditional on H6",
            "H8": "requires a physical sector-selection rule",
            "H10_particle_identification": "reserved for post-seal reveal",
        },
        "candidate_observables_file": "candidates/blind_candidate_observables.json",
    }
    json_dump(out / "blind_observables.json", observables)

    removed = []
    if cfg["output"].get("save_level") == "evidence":
        removed = remove_heavy_npz(out)

    summary = {
        "campaign_id": cfg["campaign_id"],
        "blind": True,
        "sst_inputs_used": False,
        "target_values_used": False,
        "candidate_identity_read": False,
        "sealed": False,
        "ok": True,
        "runtime": runtime_provenance(),
        "config_sha256": sha256_file(args.config),
        "candidate_manifest_sha256": sha256_file(candidate_manifest),
        "save_level": cfg["output"].get("save_level"),
        "removed_heavy_npz": removed,
        "records": records,
        "total_elapsed_s": sum(float(r["elapsed_s"]) for r in records),
    }
    json_dump(out / "blind_run_summary.json", summary)
    print("\nBLIND RUN COMPLETE. Results are not yet sealed.")
    print("Run SEAL_BLIND_RESULTS.cmd before inspecting private_reveal/.")
    print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
