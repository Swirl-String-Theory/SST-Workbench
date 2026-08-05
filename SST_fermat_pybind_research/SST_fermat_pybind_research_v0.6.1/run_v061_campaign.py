#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fermat_ext.core import write_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_step(root: Path, out: Path, index: int, name: str, cmd: list[str], expected: Path) -> dict[str, Any]:
    log = out / "logs" / f"{index:02d}_{name}.log"
    started = utc_now()
    t0 = time.perf_counter()
    with log.open("w", encoding="utf-8") as fh:
        fh.write("COMMAND: " + subprocess.list2cmdline(cmd) + "\n\n")
        proc = subprocess.Popen(
            cmd,
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
            fh.write(line)
        rc = proc.wait()
    elapsed = time.perf_counter() - t0
    ok = rc == 0 and expected.exists()
    return {
        "index": index,
        "name": name,
        "command": cmd,
        "command_line": subprocess.list2cmdline(cmd),
        "started_utc": started,
        "finished_utc": utc_now(),
        "elapsed_seconds": elapsed,
        "return_code": rc,
        "expected_output": str(expected),
        "expected_output_exists": expected.exists(),
        "status": "SUCCESS" if ok else "FAILED",
        "log": str(log),
        "log_sha256": sha256(log),
    }


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Integrated v0.6.1 full-range hole-bundle research campaign.")
    p.add_argument("--preset", choices=["smoke", "full"], default="full")
    p.add_argument("--out-root", default="v0.6.1_campaign_output")
    p.add_argument("--archive", default="SST_fermat_pybind_research_v0.6.1_results.zip")
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--resume", action="store_true")
    a = p.parse_args()
    if a.require_native and a.force_python:
        raise SystemExit("--require-native and --force-python are mutually exclusive")

    root = Path(__file__).resolve().parent
    out = root / a.out_root
    if a.overwrite:
        shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    campaign_started = utc_now()
    t0 = time.perf_counter()

    sweep_dir = out / "01_hole_bundle_sweep"
    conv_dir = out / "02_selected_convergence"
    axis_dir = out / "03_axis_robustness"
    mode_dir = out / "04_mode_projection"
    sweep_json = sweep_dir / "hole_bundle_sweep.json"
    field_cache = sweep_dir / "baseline_field_cache.npz"
    conv_json = conv_dir / "selected_convergence.json"
    axis_json = axis_dir / "axis_robustness_audit.json"
    mode_json = mode_dir / "mode_projection.json"

    common_backend: list[str] = []
    if a.require_native:
        common_backend.append("--require-native")
    if a.force_python:
        common_backend.append("--force-python")

    if a.preset == "smoke":
        sweep_extra = [
            "--centerline-points", "512",
            "--radius-ratios", "0.06125", "0.25", "0.5", "1", "2", "4", "8",
            "--circulation-ratios", "-8", "-4", "-2", "0", "2", "4", "8",
            "--top-detail-count", "16",
        ]
        convergence_extra = ["--centerline-levels", "256", "512", "--candidate-count", "4", "--gain-abs-tolerance", "0.02"]
        axis_extra = ["--offset-fractions", "0", "0.1", "--tilt-degrees", "0", "5"]
        mode_extra = ["--max-mode", "16"]
    else:
        sweep_extra = [
            "--centerline-points", "8192",
            "--radius-min", "0.06125", "--radius-max", "8",
            "--radius-count", "33", "--radius-spacing", "log",
            "--circulation-min", "-8", "--circulation-max", "8", "--circulation-step", "0.25",
            "--top-detail-count", "96",
        ]
        convergence_extra = ["--centerline-levels", "2048", "4096", "8192", "--candidate-count", "12", "--gain-abs-tolerance", "0.005"]
        axis_extra = []
        mode_extra = ["--max-mode", "64"]

    commands = [
        (
            "hole_bundle_full_range_sweep",
            [sys.executable, "run_hole_bundle_sweep.py", *sweep_extra, *common_backend, "--out-dir", str(sweep_dir)],
            sweep_json,
        ),
        (
            "selected_centerline_convergence",
            [sys.executable, "run_v061_selected_convergence.py", "--sweep-json", str(sweep_json), "--field-cache", str(field_cache), *convergence_extra, *common_backend, "--out-dir", str(conv_dir)],
            conv_json,
        ),
        (
            "axis_offset_tilt_robustness",
            [sys.executable, "run_v061_axis_audit.py", "--sweep-json", str(sweep_json), "--field-cache", str(field_cache), *axis_extra, *common_backend, "--out-dir", str(axis_dir)],
            axis_json,
        ),
        (
            "residual_mode_projection",
            [sys.executable, "run_v061_mode_projection.py", "--sweep-json", str(sweep_json), "--field-cache", str(field_cache), *mode_extra, *common_backend, "--out-dir", str(mode_dir)],
            mode_json,
        ),
    ]

    steps: list[dict[str, Any]] = []
    for index, (name, cmd, expected) in enumerate(commands, start=1):
        if a.resume and expected.exists():
            steps.append({
                "index": index,
                "name": name,
                "command": cmd,
                "command_line": subprocess.list2cmdline(cmd),
                "status": "SKIPPED_EXISTING",
                "expected_output": str(expected),
                "expected_output_exists": True,
            })
            continue
        result = run_step(root, out, index, name, cmd, expected)
        steps.append(result)
        if result["status"] != "SUCCESS":
            break

    all_success = len(steps) == len(commands) and all(s["status"] in {"SUCCESS", "SKIPPED_EXISTING"} for s in steps)
    sweep = load(sweep_json) if sweep_json.exists() else {}
    convergence = load(conv_json) if conv_json.exists() else {}
    axis = load(axis_json) if axis_json.exists() else {}
    mode = load(mode_json) if mode_json.exists() else {}

    summary = {
        "schema": "sst.fermat.v0.6.1-campaign-summary",
        "package_version": "0.6.1",
        "status": "SUCCESS" if all_success else "FAILED",
        "preset": a.preset,
        "campaign_started_utc": campaign_started,
        "campaign_finished_utc": utc_now(),
        "elapsed_seconds": time.perf_counter() - t0,
        "requested_parameter_domain": {
            "R_bundle_over_R_hole": [0.06125, 8.0],
            "Gamma_hole_over_Gamma_0": [-8.0, 8.0],
        },
        "successful_step_count": sum(1 for s in steps if s["status"] in {"SUCCESS", "SKIPPED_EXISTING"}),
        "failed_step_count": sum(1 for s in steps if s["status"] == "FAILED"),
        "steps": steps,
        "sweep_completed": sweep_json.exists(),
        "sweep_best": sweep.get("best"),
        "sweep_grid": sweep.get("grid"),
        "selected_convergence_completed": conv_json.exists(),
        "selected_convergence_best_finest": convergence.get("best_finest"),
        "any_gain_converged": convergence.get("any_gain_converged", False),
        "axis_robustness_completed": axis_json.exists(),
        "all_tested_axis_perturbations_stabilizing": axis.get("all_tested_perturbations_remain_stabilizing", False),
        "mode_projection_completed": mode_json.exists(),
        "mode_total_residual_energy_gain": mode.get("total_residual_energy_gain"),
        "physical_finite_closed_bundle_certified": False,
        "global_closed_orbit_certified": False,
        "monodromy_certified": False,
        "qsm_certified": False,
        "epistemic_status": "RESEARCH_TRACK",
    }
    write_json(out / "campaign_summary.json", summary)

    output_files = []
    for path in sorted(out.rglob("*")):
        if path.is_file():
            output_files.append({
                "path": path.relative_to(out).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    manifest = {
        "schema": "sst.fermat.v0.6.1-integrated-manifest",
        "package_version": "0.6.1",
        "campaign_root": out.name,
        "created_utc": utc_now(),
        "python": sys.version,
        "platform": sys.platform,
        "preset": a.preset,
        "steps": steps,
        "files": output_files,
    }
    write_json(out / "campaign_manifest.json", manifest)

    if all_success:
        archive = root / a.archive
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            for path in sorted(out.rglob("*")):
                if path.is_file():
                    z.write(path, (Path(out.name) / path.relative_to(out)).as_posix())
        digest = sha256(archive)
        (archive.with_suffix(archive.suffix + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
        summary["archive"] = str(archive)
        summary["archive_sha256"] = digest
        write_json(out / "campaign_summary.json", summary)

    print(json.dumps(summary, indent=2))
    return 0 if all_success else 2


if __name__ == "__main__":
    raise SystemExit(main())
