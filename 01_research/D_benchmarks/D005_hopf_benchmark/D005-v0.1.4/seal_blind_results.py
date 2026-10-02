#!/usr/bin/env python3
"""Seal blind results by hashing code, config, inputs and the complete result tree."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from blind_utils import (
    code_digest,
    json_dump,
    json_load,
    sha256_file,
    tree_digest,
    validate_blind_config,
)

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--candidate-manifest", type=Path, default=Path("blind_inputs/candidate_pack_manifest.json"))
    p.add_argument("--result-root", type=Path, default=Path("results/blind"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = json_load(args.config)
    validate_blind_config(cfg)
    summary_path = args.result_root / "blind_run_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError("No blind_run_summary.json; run the blind campaign first.")
    summary = json_load(summary_path)
    if not summary.get("ok"):
        raise RuntimeError("Blind run did not complete successfully.")
    if summary.get("sst_inputs_used") is not False or summary.get("target_values_used") is not False:
        raise RuntimeError("Refusing to seal: blind summary does not certify zero SST/target inputs.")
    if summary.get("candidate_identity_read") is not False:
        raise RuntimeError("Refusing to seal: candidate identity was reported as read.")

    manifest = json_load(args.candidate_manifest)
    commitment = manifest.get("private_key_commitment_sha256")
    if not commitment:
        raise RuntimeError("Candidate manifest lacks private-key commitment.")

    # A narrow leakage scan over blind candidate observables.
    candidate_obs = args.result_root / "candidates/blind_candidate_observables.json"
    if candidate_obs.exists():
        raw = candidate_obs.read_text(encoding="utf-8").lower()
        forbidden_literals = ["\"knot_type\"", "\"electron\"", "\"proton\"", "\"neutron\"", "t(2,3)", "\"3_1\"", "\"4_1\"", "\"5_1\"", "\"7_1\""]
        leaked = [x for x in forbidden_literals if x in raw]
        if leaked:
            raise RuntimeError(f"Identity leakage detected in blind candidate observables: {leaked}")

    result_digest, result_records = tree_digest(
        args.result_root,
        exclude_names={"SEALED_MANIFEST.json", "BLIND_RESULT_SHA256.txt"},
        exclude_dirs={"reveal"},
    )
    code_sha, code_records = code_digest(ROOT)

    sealed = {
        "campaign_id": cfg["campaign_id"],
        "status": "SEALED",
        "sealed_utc": datetime.now(timezone.utc).isoformat(),
        "sst_inputs_used": False,
        "target_values_used": False,
        "candidate_identity_read": False,
        "config_sha256": sha256_file(args.config),
        "candidate_manifest_sha256": sha256_file(args.candidate_manifest),
        "private_key_commitment_sha256": commitment,
        "code_sha256": code_sha,
        "result_tree_sha256": result_digest,
        "code_files": code_records,
        "result_files": result_records,
        "rule": "Any post-seal modification of blind result files invalidates reveal comparison.",
    }
    json_dump(args.result_root / "SEALED_MANIFEST.json", sealed)
    (args.result_root / "BLIND_RESULT_SHA256.txt").write_text(
        f"{result_digest}  blind_result_tree\n", encoding="utf-8"
    )
    print("BLIND RESULTS SEALED")
    print(f"result_tree_sha256={result_digest}")
    print(f"code_sha256={code_sha}")
    print("It is now permissible to inspect private_reveal/ or supply reveal inputs.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
