#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW_STAGES = [(160, 960), (192, 1152)]
DEFAULT_IDS = ["L6n1", "L6a4", "L4a1"]

def flatten(values):
    if values is None:
        return list(DEFAULT_IDS)
    out = []
    for value in values:
        out.extend(x.strip() for x in str(value).split(",") if x.strip())
    return out

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def rel(a, b):
    a, b = float(a), float(b)
    return abs(a-b) / max(abs(a), abs(b), 1e-12)

def find_previous(explicit):
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = ROOT / p
        return p if p.exists() else None
    candidates = [
        p for p in ROOT.glob("outputs_qm_spectral_ladder_*")
        if (p / "m128_N768" / "sector_readiness.csv").exists()
    ]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None

def load_stage(stage_dir):
    path = stage_dir / "sector_readiness.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return {(r["link_id"], r["signs"]): r for r in read_csv(path)}

def compare(stage_rows, re_threshold, gradient_threshold):
    rows = []
    ordered = sorted(stage_rows)
    for lo, hi in zip(ordered, ordered[1:]):
        for key in sorted(set(stage_rows[lo]) & set(stage_rows[hi])):
            a, b = stage_rows[lo][key], stage_rows[hi][key]
            re_rel = rel(a["relative_equilibrium_score"], b["relative_equilibrium_score"])
            grad_rel = rel(a["primary_gradient_norm"], b["primary_gradient_norm"])
            neg_equal = int(a["hessian_negative_modes"]) == int(b["hessian_negative_modes"])
            rank_equal = (int(a["symplectic_rank"]), int(a["symplectic_dimension"])) == (
                int(b["symplectic_rank"]), int(b["symplectic_dimension"])
            )
            unstable_equal = int(a["unstable_linear_modes"]) == int(b["unstable_linear_modes"])
            step_ok = str(a["step_convergence_pass"]).lower() == "true" and str(b["step_convergence_pass"]).lower() == "true"
            passed = re_rel <= re_threshold and grad_rel <= gradient_threshold and neg_equal and rank_equal and unstable_equal and step_ok
            rows.append({
                "link_id": key[0], "signs": key[1],
                "cutoff_from": lo, "cutoff_to": hi,
                "relative_equilibrium_relative_difference": re_rel,
                "primary_gradient_relative_difference": grad_rel,
                "negative_mode_count_agreement": neg_equal,
                "symplectic_rank_agreement": rank_equal,
                "unstable_mode_count_agreement": unstable_equal,
                "both_step_converged": step_ok,
                "cutoff_stability_pass": passed,
            })
    return rows

def main():
    ap = argparse.ArgumentParser(description="Run only the m160/N960 and m192/N1152 continuation of the matched full-Hessian spectral ladder.")
    ap.add_argument("--ids", "-Ids", nargs="*", default=None)
    ap.add_argument("--native-threads", "-NativeThreads", type=int, default=16)
    ap.add_argument("--previous", "-Previous", default=None)
    ap.add_argument("--output", "-Output", default=None)
    ap.add_argument("--re-threshold", "-ReThreshold", type=float, default=0.05)
    ap.add_argument("--gradient-threshold", "-GradientThreshold", type=float, default=0.15)
    ap.add_argument("--no-baseline", "-NoBaseline", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ids = flatten(args.ids)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outroot = Path(args.output) if args.output else ROOT / f"outputs_qm_spectral_extended_{stamp}"
    if not outroot.is_absolute():
        outroot = ROOT / outroot
    outroot.mkdir(parents=True, exist_ok=True)

    previous = None if args.no_baseline else find_previous(args.previous)
    if not args.no_baseline and previous is None:
        print("[SST] ERROR: no prior outputs_qm_spectral_ladder_* with m128_N768 found. Use -Previous <folder> or -NoBaseline.", file=sys.stderr)
        return 2

    stage_rows = {}
    if previous is not None:
        baseline_dir = previous / "m128_N768"
        stage_rows[128] = load_stage(baseline_dir)
        print(f"[SST] reusing m<=128 baseline: {baseline_dir}", flush=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    commands = []
    for cutoff, n in NEW_STAGES:
        stage = outroot / f"m{cutoff}_N{n}"
        cfg = ROOT / "configs" / f"qm_full_filtered_m{cutoff}.json"
        commands.append([
            sys.executable, "-m", "sst_link_suite.qm_cli",
            "--input", str(ROOT / "data" / "idealLinks.txt"),
            "--output", str(stage),
            "--config", str(cfg),
            "--ids", *ids,
            "--require-native", "--skip-native-build",
            "--native-threads", str(args.native_threads),
        ])

    if args.dry_run:
        plan = {
            "ids": ids,
            "baseline": str(previous) if previous else None,
            "stages": [{"cutoff": c, "qm_sample_n": n} for c, n in NEW_STAGES],
            "commands": commands,
        }
        (outroot / "extended_ladder_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
        for command in commands:
            print(" ".join(map(str, command)))
        return 0

    for (cutoff, n), command in zip(NEW_STAGES, commands):
        stage = outroot / f"m{cutoff}_N{n}"
        print(f"\n[SST] extended cutoff m<={cutoff}, N={n}", flush=True)
        rc = subprocess.run(command, cwd=ROOT, env=env).returncode
        if rc:
            return rc
        stage_rows[cutoff] = load_stage(stage)

    comparisons = compare(stage_rows, args.re_threshold, args.gradient_threshold)
    if comparisons:
        with (outroot / "spectral_extended_comparison.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(comparisons[0]))
            w.writeheader()
            w.writerows(comparisons)

    summary = []
    for link_id in ids:
        rows = [r for r in comparisons if r["link_id"] == link_id]
        summary.append({
            "link_id": link_id,
            "comparison_rows": len(rows),
            "all_sector_extended_cutoff_stability_pass": bool(rows) and all(r["cutoff_stability_pass"] for r in rows),
            "failed_rows": sum(not r["cutoff_stability_pass"] for r in rows),
            "comparisons_present": sorted({f"{r['cutoff_from']}->{r['cutoff_to']}" for r in rows}),
            "status": "[RESEARCH TRACK NUMERICAL REGULARIZATION] Cutoff convergence is not a physical SST cutoff derivation.",
        })

    (outroot / "spectral_extended_ladder_summary.json").write_text(
        json.dumps({
            "ids": ids,
            "baseline_source": str(previous) if previous else None,
            "stages_present": sorted(stage_rows),
            "summary": summary,
        }, indent=2), encoding="utf-8"
    )

    print("\n[SST] extended cutoff-stability summary")
    for row in summary:
        print(f"{row['link_id']:6s} pass={row['all_sector_extended_cutoff_stability_pass']} failed_rows={row['failed_rows']}")
    print(f"[SST] output: {outroot}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
