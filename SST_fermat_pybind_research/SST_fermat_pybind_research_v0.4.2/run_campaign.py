#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fermat_ext.core import PACKAGE_VERSION, write_json


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_step(name: str, command: list[str], root: Path, logs: Path, expected: Path) -> dict:
    started = now()
    log_path = logs / f"{name}.log"
    with log_path.open("w", encoding="utf-8") as fh:
        fh.write(f"[{started}] COMMAND: {shlex.join(command)}\n")
        proc = subprocess.run(command, cwd=Path(__file__).resolve().parent, text=True, stdout=fh, stderr=subprocess.STDOUT)
        completed = now()
        fh.write(f"\n[{completed}] EXIT_CODE={proc.returncode}\n")
    return {
        "name": name,
        "command": command,
        "command_text": shlex.join(command),
        "started_utc": started,
        "completed_utc": completed,
        "exit_code": proc.returncode,
        "expected_output": str(expected),
        "expected_output_exists": expected.exists(),
        "status": "SUCCESS" if proc.returncode == 0 and expected.exists() else "FAILED",
        "log": str(log_path),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Run the v0.4.2 candidate-certification campaign.")
    p.add_argument("--preset", choices=("hotfix", "smoke", "full"), default="hotfix")
    p.add_argument("--output-root", default="v0.4.2_campaign_output")
    p.add_argument("--no-archive", action="store_true")
    p.add_argument("--continue-on-error", action="store_true")
    a = p.parse_args()
    root = Path(a.output_root).resolve(); root.mkdir(parents=True, exist_ok=True)
    logs = root / "logs"; logs.mkdir(exist_ok=True)
    py = sys.executable
    common = ["--no-auto-build", "--require-native"]

    steps: list[tuple[str, list[str], Path]] = []
    if a.preset in ("smoke", "full"):
        steps.extend([
            ("01_audit", [py, "run_all_checks.py", "--out-dir", str(root/"audit_out_native"), *common], root/"audit_out_native/audit_summary.json"),
            ("02_candidate_atlas", [py, "run_candidate_atlas.py", "--epsilon", "0.0019", "--centerline-points", "2048" if a.preset=="smoke" else "8192", "--stations", "2" if a.preset=="smoke" else "8", "--angles", "6" if a.preset=="smoke" else "16", "--bracket-samples", "64" if a.preset=="smoke" else "96", "--out-dir", str(root/"candidate_atlas_0019"), *common], root/"candidate_atlas_0019/candidate_atlas.json"),
        ])
    if a.preset == "full":
        steps.extend([
            ("03_candidate_atlas_high", [py, "run_candidate_atlas.py", "--epsilon", "0.0019", "--centerline-points", "16384", "--stations", "32", "--angles", "32", "--bracket-samples", "128", "--out-dir", str(root/"candidate_atlas_0019_high"), *common], root/"candidate_atlas_0019_high/candidate_atlas.json"),
            ("04_convergence", [py, "run_candidate_convergence.py", "--epsilon", "0.0019", "--point-counts", "4096", "8192", "16384", "--stations", "8", "--angles", "16", "--bracket-samples", "96", "--out-dir", str(root/"convergence_0019"), *common], root/"convergence_0019/convergence_report.json"),
            ("05_convergence_high", [py, "run_candidate_convergence.py", "--knots", "3_1", "4_1", "5_2", "--epsilon", "0.0019", "--point-counts", "8192", "16384", "32768", "--stations", "8", "--angles", "16", "--bracket-samples", "96", "--out-dir", str(root/"convergence_0019_high"), *common], root/"convergence_0019_high/convergence_report.json"),
        ])

    # The hotfix preset reruns only the v0.4.1 step that failed.
    bifurcation_points = ("2048", "4096") if a.preset == "smoke" else ("32768", "65536")
    epsilon_stop = "0.00185" if a.preset == "smoke" else "0.00210"
    epsilon_step = "0.00005" if a.preset == "smoke" else "0.000025"
    steps.append((
        "06_bifurcation_atlas",
        [py, "run_bifurcation_atlas.py", "--epsilon-start", "0.00180", "--epsilon-stop", epsilon_stop,
         "--epsilon-step", epsilon_step, "--resolution-mode", "adaptive",
         "--target-ds-over-epsilon", "0.5", "--min-centerline-points", bifurcation_points[0],
         "--max-centerline-points", bifurcation_points[1], "--round-centerline-points-to", "1024",
         "--stations", "2" if a.preset=="smoke" else "8", "--angles", "6" if a.preset=="smoke" else "16",
         "--bracket-samples", "64" if a.preset=="smoke" else "96",
         "--out-dir", str(root/"bifurcation_atlas"), *common],
        root/"bifurcation_atlas/bifurcation_atlas.json",
    ))
    if a.preset == "full":
        steps.extend([
            ("07_scale_sweep", [py, "run_scale_sweep.py", "--scales", "0.5", "1.0", "2.0", "4.0", "--epsilon", "0.0019", "--resolution-mode", "adaptive", "--target-ds-over-epsilon", "1.0", "--min-centerline-points", "4096", "--max-centerline-points", "65536", "--round-centerline-points-to", "1024", "--stations", "8", "--angles", "16", "--bracket-samples", "96", "--out-dir", str(root/"scale_sweep_0019"), *common], root/"scale_sweep_0019/scale_sweep.json"),
            ("08_symmetry_audit", [py, "run_symmetry_audit.py", "--epsilon", "0.0019", "--centerline-points", "4096", "--out-dir", str(root/"symmetry_audit"), *common], root/"symmetry_audit/symmetry_audit.json"),
        ])

    manifest = {
        "schema": "sst.fermat.campaign-manifest.v0.4.2",
        "package_version": PACKAGE_VERSION,
        "preset": a.preset,
        "started_utc": now(),
        "status": "RUNNING",
        "steps": [],
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    for name, command, expected in steps:
        result = run_step(name, command, root, logs, expected)
        manifest["steps"].append(result)
        write_json(root/"campaign_manifest.json", manifest)
        if result["status"] != "SUCCESS" and not a.continue_on_error:
            break
    manifest["completed_utc"] = now()
    manifest["successful_step_count"] = sum(s["status"] == "SUCCESS" for s in manifest["steps"])
    manifest["failed_step_count"] = sum(s["status"] != "SUCCESS" for s in manifest["steps"])
    manifest["status"] = "SUCCESS" if manifest["failed_step_count"] == 0 and len(manifest["steps"]) == len(steps) else "FAILED_OR_PARTIAL"
    write_json(root/"campaign_manifest.json", manifest)
    summary = {
        "package_version": PACKAGE_VERSION,
        "preset": a.preset,
        "status": manifest["status"],
        "successful_step_count": manifest["successful_step_count"],
        "failed_step_count": manifest["failed_step_count"],
        "output_root": str(root),
        "archive_requested": not a.no_archive,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(root/"campaign_summary.json", summary)
    if not a.no_archive:
        archive = root.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in root.rglob("*"):
                if path.is_file(): zf.write(path, path.relative_to(root.parent))
        summary["archive"] = str(archive)
        write_json(root/"campaign_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if manifest["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
