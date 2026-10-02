#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STAGES = {
    "max": [
        {
            "name": "max_128_256_512",
            "sample_ns": [128, 256, 512],
            "tolerance": 0.03,
        },
    ],
    "ladder": [
        {
            "name": "max_128_256_512",
            "sample_ns": [128, 256, 512],
            "tolerance": 0.03,
        },
        {
            "name": "deep_192_384_768",
            "sample_ns": [192, 384, 768],
            "tolerance": 0.02,
        },
        {
            "name": "ultra_256_512_1024",
            "sample_ns": [256, 512, 1024],
            "tolerance": 0.015,
        },
    ],
    "ultra": [
        {
            "name": "ultra_256_512_1024",
            "sample_ns": [256, 512, 1024],
            "tolerance": 0.015,
        },
    ],
}


def load_base_config() -> dict:
    path = ROOT / "configs" / "qm_max.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Expected v0.3.3 max config at {path}. "
            "Place this runner in the root of SST_ideal_links_comprehensive_test_suite_v0.3.3."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_stage_config(base: dict, stage: dict, path: Path) -> None:
    cfg = dict(base)
    cfg["name"] = f"continuum_{stage['name']}"
    cfg["continuum_sample_ns"] = list(stage["sample_ns"])
    cfg["continuum_relative_tolerance"] = float(stage["tolerance"])
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def run_stage(stage: dict, ids: list[str], output_root: Path, base: dict) -> list[dict]:
    stage_dir = output_root / stage["name"]
    stage_dir.mkdir(parents=True, exist_ok=True)
    config_path = stage_dir / "config_used.json"
    write_stage_config(base, stage, config_path)

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_continuum.py"),
        "--config", str(config_path),
        "--output", str(stage_dir),
        "--require-native",
        "--skip-native-build",
        "--ids",
        *ids,
    ]

    print()
    print("=" * 78)
    print(f"Stage: {stage['name']}")
    print(f"N ladder: {stage['sample_ns']}")
    print(f"Tolerance: {stage['tolerance']:.3%}")
    print(f"Links: {' '.join(ids)}")
    print("=" * 78)
    print(" ".join(map(str, cmd)), flush=True)

    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Continuum stage {stage['name']} failed with return code {proc.returncode}"
        )

    summary = stage_dir / "continuum_summary.csv"
    if not summary.exists():
        raise RuntimeError(f"Missing stage summary: {summary}")

    with summary.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        row["stage"] = stage["name"]
        row["stage_sample_ns"] = ",".join(map(str, stage["sample_ns"]))
        row["stage_tolerance"] = stage["tolerance"]
    return rows


def bool_csv(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Adaptive SST v0.3.3 continuum ladder. "
            "Only links that fail a stage advance to the next resolution."
        )
    )
    ap.add_argument(
        "--mode",
        choices=sorted(STAGES),
        default="ladder",
        help=(
            "max = [128,256,512]; "
            "ladder = adaptive max -> [192,384,768] -> [256,512,1024]; "
            "ultra = [256,512,1024] directly."
        ),
    )
    ap.add_argument(
        "--ids",
        nargs="+",
        default=["L6a4", "L4a1", "L6n1", "L7n2"],
    )
    ap.add_argument(
        "--output",
        default=None,
        help="Output root. Default: timestamped outputs_continuum_<mode>_YYYYMMDD_HHMMSS",
    )
    args = ap.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_root = (
        Path(args.output)
        if args.output
        else ROOT / f"outputs_continuum_{args.mode}_{timestamp}"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    base = load_base_config()
    remaining = list(dict.fromkeys(args.ids))
    all_rows: list[dict] = []
    last_row_by_id: dict[str, dict] = {}

    for stage in STAGES[args.mode]:
        if not remaining:
            print("\nAll links already passed; higher-resolution stages skipped.")
            break

        rows = run_stage(stage, remaining, output_root, base)
        all_rows.extend(rows)

        failed: list[str] = []
        for row in rows:
            link_id = row["link_id"]
            last_row_by_id[link_id] = row
            passed = bool_csv(row["continuum_pass"])
            rel = float(row["max_last_pair_relative_difference"])
            status = "PASS" if passed else "FAIL -> advance"
            print(f"{link_id:6s}  {rel:10.4%}  {status}")
            if not passed:
                failed.append(link_id)

        remaining = failed

    combined_path = output_root / "continuum_ladder_all_stages.csv"
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        with combined_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    final_rows = []
    for link_id in args.ids:
        row = last_row_by_id.get(link_id)
        if row is None:
            final_rows.append({
                "link_id": link_id,
                "final_stage": "",
                "final_sample_ns": "",
                "final_tolerance": "",
                "final_relative_difference": "",
                "continuum_pass": False,
                "status": "NOT_RUN",
            })
            continue
        passed = bool_csv(row["continuum_pass"])
        final_rows.append({
            "link_id": link_id,
            "final_stage": row["stage"],
            "final_sample_ns": row["stage_sample_ns"],
            "final_tolerance": row["stage_tolerance"],
            "final_relative_difference": row["max_last_pair_relative_difference"],
            "continuum_pass": passed,
            "status": "PASS" if passed else "NOT_CONVERGED_AT_MAX_LADDER",
        })

    final_path = output_root / "continuum_ladder_final.csv"
    with final_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(final_rows[0].keys()))
        writer.writeheader()
        writer.writerows(final_rows)

    metadata = {
        "mode": args.mode,
        "ids": args.ids,
        "stages": STAGES[args.mode],
        "adaptive_rule": (
            "A link advances only when continuum_pass is false at the current stage. "
            "PASS refers only to v0.3.3 baseline continuum diagnostics and the stage tolerance."
        ),
        "final": final_rows,
    }
    (output_root / "continuum_ladder_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print()
    print("=" * 78)
    print("FINAL CONTINUUM LADDER")
    print("=" * 78)
    failed_final = 0
    for row in final_rows:
        rel = row["final_relative_difference"]
        rel_text = f"{float(rel):.4%}" if rel != "" else "n/a"
        print(
            f"{row['link_id']:6s}  "
            f"{row['status']:28s}  "
            f"{row['final_stage']:24s}  "
            f"{rel_text}"
        )
        if row["status"] != "PASS":
            failed_final += 1

    print(f"\nOutput: {output_root}")
    print(f"Combined ledger: {combined_path}")
    print(f"Final ledger:    {final_path}")

    # Numerical non-convergence is a scientific result, not a process error.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
