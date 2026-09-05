#!/usr/bin/env python3
"""Sequential v0.4.3 campaign runner with logging, resume support, and ZIP packaging."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fermat_ext import __version__


@dataclass(frozen=True)
class Step:
    name: str
    arguments: tuple[str, ...]
    expected_relative_output: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_text(command: Iterable[str]) -> str:
    return subprocess.list2cmdline(list(command)) if os.name == "nt" else shlex.join(list(command))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_common_native_flags(args: list[str], require_native: bool) -> None:
    args.append("--no-auto-build")
    if require_native:
        args.append("--require-native")


def full_steps(python_exe: str, out_root: Path, require_native: bool, skip_build: bool) -> list[Step]:
    steps: list[Step] = []
    if not skip_build:
        steps.append(Step(
            "00_build_native",
            (python_exe, "-m", "fermat_ext.build_ext_if_needed", "--force", "--strict"),
        ))

    def script_step(name: str, script: str, arguments: list[str], expected: str) -> None:
        add_common_native_flags(arguments, require_native)
        steps.append(Step(name, tuple([python_exe, script, *arguments]), expected))

    script_step(
        "01_audit_out_native", "run_all_checks.py",
        ["--out-dir", str(out_root / "audit_out_native")],
        "audit_out_native/audit_summary.json",
    )
    script_step(
        "02_candidate_atlas_0019", "run_candidate_atlas.py",
        [
            "--epsilon", "0.0019", "--centerline-points", "8192",
            "--stations", "8", "--angles", "16", "--bracket-samples", "96",
            "--out-dir", str(out_root / "candidate_atlas_0019"),
        ],
        "candidate_atlas_0019/candidate_atlas.json",
    )
    script_step(
        "03_candidate_atlas_0019_high", "run_candidate_atlas.py",
        [
            "--epsilon", "0.0019", "--centerline-points", "16384",
            "--stations", "32", "--angles", "32", "--bracket-samples", "128",
            "--out-dir", str(out_root / "candidate_atlas_0019_high"),
        ],
        "candidate_atlas_0019_high/candidate_atlas.json",
    )
    script_step(
        "04_convergence_0019", "run_candidate_convergence.py",
        [
            "--epsilon", "0.0019", "--point-counts", "4096", "8192", "16384",
            "--stations", "8", "--angles", "16", "--bracket-samples", "96",
            "--out-dir", str(out_root / "convergence_0019"),
        ],
        "convergence_0019/convergence_report.json",
    )
    # v0.4.3 correction: include 3_1 in the high-resolution three-level gate.
    script_step(
        "05_convergence_0019_high", "run_candidate_convergence.py",
        [
            "--knots", "3_1", "4_1", "5_2",
            "--epsilon", "0.0019", "--point-counts", "8192", "16384", "32768",
            "--stations", "8", "--angles", "16", "--bracket-samples", "96",
            "--out-dir", str(out_root / "convergence_0019_high"),
        ],
        "convergence_0019_high/convergence_report.json",
    )
    # Conservative resolution near the straight-filament branch-loss threshold.
    script_step(
        "06_bifurcation_atlas", "run_bifurcation_atlas.py",
        [
            "--epsilon-start", "0.00180", "--epsilon-stop", "0.00210",
            "--epsilon-step", "0.000025", "--resolution-mode", "adaptive",
            "--target-ds-over-epsilon", "0.5",
            "--min-centerline-points", "32768", "--max-centerline-points", "65536",
            "--round-centerline-points-to", "1024",
            "--stations", "8", "--angles", "16", "--bracket-samples", "96",
            "--out-dir", str(out_root / "bifurcation_atlas"),
        ],
        "bifurcation_atlas/bifurcation_atlas.json",
    )
    # Scale sweep now preserves a controlled mean segment-length/epsilon ratio.
    script_step(
        "07_scale_sweep_0019", "run_scale_sweep.py",
        [
            "--scales", "0.5", "1.0", "2.0", "4.0", "--epsilon", "0.0019",
            "--resolution-mode", "adaptive", "--target-ds-over-epsilon", "1.0",
            "--min-centerline-points", "4096", "--max-centerline-points", "65536",
            "--round-centerline-points-to", "1024",
            "--stations", "8", "--angles", "16", "--bracket-samples", "96",
            "--out-dir", str(out_root / "scale_sweep_0019"),
        ],
        "scale_sweep_0019/scale_sweep.json",
    )
    script_step(
        "08_symmetry_audit", "run_symmetry_audit.py",
        [
            "--epsilon", "0.0019", "--centerline-points", "4096",
            "--out-dir", str(out_root / "symmetry_audit"),
        ],
        "symmetry_audit/symmetry_audit.json",
    )
    return steps


def smoke_steps(python_exe: str, out_root: Path, require_native: bool, skip_build: bool) -> list[Step]:
    steps: list[Step] = []
    if not skip_build:
        steps.append(Step(
            "00_build_native",
            (python_exe, "-m", "fermat_ext.build_ext_if_needed", "--force", "--strict"),
        ))

    def script_step(name: str, script: str, arguments: list[str], expected: str) -> None:
        add_common_native_flags(arguments, require_native)
        steps.append(Step(name, tuple([python_exe, script, *arguments]), expected))

    script_step("01_audit_out_native", "run_all_checks.py",
                ["--out-dir", str(out_root / "audit_out_native")],
                "audit_out_native/audit_summary.json")
    script_step("02_candidate_smoke", "run_candidate_atlas.py",
                ["--knots", "0_1", "--epsilon", "0.0019", "--centerline-points", "1024",
                 "--stations", "1", "--angles", "3", "--bracket-samples", "48",
                 "--out-dir", str(out_root / "candidate_smoke")],
                "candidate_smoke/candidate_atlas.json")
    script_step("03_convergence_smoke", "run_candidate_convergence.py",
                ["--knots", "0_1", "--epsilon", "0.0019", "--point-counts", "256", "512", "1024",
                 "--stations", "1", "--angles", "3", "--bracket-samples", "48",
                 "--out-dir", str(out_root / "convergence_smoke")],
                "convergence_smoke/convergence_report.json")
    script_step("04_bifurcation_smoke", "run_bifurcation_atlas.py",
                ["--knots", "0_1", "--epsilon-values", "0.0019", "0.0020",
                 "--resolution-mode", "fixed", "--centerline-points", "512",
                 "--stations", "1", "--angles", "3", "--bracket-samples", "48",
                 "--out-dir", str(out_root / "bifurcation_smoke")],
                "bifurcation_smoke/bifurcation_atlas.json")
    script_step("05_scale_smoke", "run_scale_sweep.py",
                ["--knots", "0_1", "--scales", "1.0", "2.0", "--epsilon", "0.0019",
                 "--resolution-mode", "adaptive", "--min-centerline-points", "512",
                 "--max-centerline-points", "2048", "--stations", "1", "--angles", "3",
                 "--bracket-samples", "48", "--out-dir", str(out_root / "scale_smoke")],
                "scale_smoke/scale_sweep.json")
    script_step("06_symmetry_smoke", "run_symmetry_audit.py",
                ["--knots", "0_1", "--epsilon", "0.0019", "--centerline-points", "256",
                 "--out-dir", str(out_root / "symmetry_smoke")],
                "symmetry_smoke/symmetry_audit.json")
    return steps


def run_step(step: Step, *, cwd: Path, log_path: Path) -> tuple[int, float]:
    start = time.perf_counter()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        header = f"[{utc_now()}] COMMAND: {command_text(step.arguments)}\n"
        print(header.rstrip())
        log.write(header)
        log.flush()
        process = subprocess.Popen(
            list(step.arguments),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)
        rc = process.wait()
        duration = time.perf_counter() - start
        footer = f"\n[{utc_now()}] EXIT_CODE={rc} DURATION_SECONDS={duration:.3f}\n"
        print(footer.rstrip())
        log.write(footer)
    return rc, duration


def create_archive(out_root: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = archive_path.with_suffix(archive_path.suffix + ".tmp")
    temp_path.unlink(missing_ok=True)
    archive_path.unlink(missing_ok=True)
    with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for path in sorted(out_root.rglob("*")):
            if path.is_file():
                arcname = Path(out_root.name) / path.relative_to(out_root)
                zf.write(path, arcname.as_posix())
    temp_path.replace(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the complete SST Fermat v0.4.3 campaign sequentially and ZIP all outputs."
    )
    parser.add_argument("--preset", choices=("full", "smoke"), default="full")
    parser.add_argument("--out-root", default="v0.4.3_campaign_output")
    parser.add_argument("--archive", default="SST_fermat_pybind_research_v0.4.3_results.zip")
    parser.add_argument("--python", dest="python_exe", default=sys.executable)
    parser.add_argument("--require-native", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--no-zip", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = (project_root / out_root).resolve()
    archive_path = Path(args.archive)
    if not archive_path.is_absolute():
        archive_path = (project_root / archive_path).resolve()

    if args.overwrite:
        shutil.rmtree(out_root, ignore_errors=True)
        archive_path.unlink(missing_ok=True)
    elif out_root.exists() and any(out_root.iterdir()) and not args.resume:
        raise SystemExit(
            f"output root already contains files: {out_root}\n"
            "Use --resume to continue or --overwrite to start clean."
        )

    out_root.mkdir(parents=True, exist_ok=True)
    logs_dir = out_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    steps = (
        full_steps(args.python_exe, out_root, args.require_native, args.skip_build)
        if args.preset == "full"
        else smoke_steps(args.python_exe, out_root, args.require_native, args.skip_build)
    )

    environment = {
        "package_version": __version__,
        "preset": args.preset,
        "project_root": str(project_root),
        "output_root": str(out_root),
        "archive": str(archive_path),
        "python_executable": args.python_exe,
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "require_native": args.require_native,
        "started_utc": utc_now(),
    }
    write_json(out_root / "environment.json", environment)
    (out_root / "campaign_commands.txt").write_text(
        "\n".join(command_text(step.arguments) for step in steps) + "\n", encoding="utf-8"
    )

    manifest = {
        "schema": "sst.fermat.campaign-manifest.v0.4.3",
        "package_version": __version__,
        "preset": args.preset,
        "started_utc": environment["started_utc"],
        "completed_utc": None,
        "status": "RUNNING",
        "steps": [],
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }
    write_json(out_root / "campaign_manifest.json", manifest)

    if args.dry_run:
        for step in steps:
            print(f"{step.name}: {command_text(step.arguments)}")
        manifest["status"] = "DRY_RUN"
        manifest["completed_utc"] = utc_now()
        write_json(out_root / "campaign_manifest.json", manifest)
        return 0

    failed = False
    for step in steps:
        marker = logs_dir / f"{step.name}.success.json"
        expected = out_root / step.expected_relative_output if step.expected_relative_output else None
        if args.resume and marker.exists() and (expected is None or expected.exists()):
            record = json.loads(marker.read_text(encoding="utf-8"))
            record["resume_action"] = "SKIPPED_ALREADY_SUCCESSFUL"
            manifest["steps"].append(record)
            write_json(out_root / "campaign_manifest.json", manifest)
            print(f"[resume] {step.name}: already successful; skipped")
            continue

        started = utc_now()
        rc, duration = run_step(step, cwd=project_root, log_path=logs_dir / f"{step.name}.log")
        expected_ok = expected is None or expected.exists()
        success = rc == 0 and expected_ok
        record = {
            "name": step.name,
            "command": list(step.arguments),
            "command_text": command_text(step.arguments),
            "started_utc": started,
            "completed_utc": utc_now(),
            "duration_seconds": duration,
            "exit_code": rc,
            "expected_output": str(expected) if expected else None,
            "expected_output_exists": expected_ok,
            "status": "SUCCESS" if success else "FAILED",
            "log": str(logs_dir / f"{step.name}.log"),
        }
        manifest["steps"].append(record)
        write_json(out_root / "campaign_manifest.json", manifest)
        if success:
            write_json(marker, record)
        else:
            failed = True
            if not args.keep_going:
                break

    manifest["completed_utc"] = utc_now()
    manifest["status"] = "FAILED_OR_PARTIAL" if failed else "SUCCESS"
    manifest["successful_step_count"] = sum(r.get("status") == "SUCCESS" for r in manifest["steps"])
    manifest["failed_step_count"] = sum(r.get("status") == "FAILED" for r in manifest["steps"])
    write_json(out_root / "campaign_manifest.json", manifest)
    write_json(out_root / "campaign_summary.json", {
        "package_version": __version__,
        "preset": args.preset,
        "status": manifest["status"],
        "successful_step_count": manifest["successful_step_count"],
        "failed_step_count": manifest["failed_step_count"],
        "output_root": str(out_root),
        "archive_requested": not args.no_zip,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    })

    if not args.no_zip:
        print(f"Creating results archive: {archive_path}")
        create_archive(out_root, archive_path)
        digest = sha256_file(archive_path)
        archive_path.with_suffix(archive_path.suffix + ".sha256").write_text(
            f"{digest}  {archive_path.name}\n", encoding="utf-8"
        )
        print(f"Archive SHA-256: {digest}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
