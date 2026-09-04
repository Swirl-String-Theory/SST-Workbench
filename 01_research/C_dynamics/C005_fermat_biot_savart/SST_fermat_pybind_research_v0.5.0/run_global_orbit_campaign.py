#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
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

from fermat_ext import __version__
from fermat_ext.core import write_json


@dataclass(frozen=True)
class Step:
    name: str
    arguments: tuple[str, ...]
    expected_relative_output: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_text(arguments: tuple[str, ...]) -> str:
    return subprocess.list2cmdline(list(arguments)) if sys.platform == "win32" else shlex.join(arguments)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_backend_flags(arguments: list[str], require_native: bool, skip_build: bool) -> None:
    if skip_build:
        arguments.append("--no-auto-build")
    if require_native:
        arguments.append("--require-native")


def campaign_steps(python_exe: str, out_root: Path, *, preset: str, require_native: bool, skip_build: bool) -> list[Step]:
    steps: list[Step] = []

    def add(name: str, script: str, args: list[str], expected: str, *, native_flags: bool = True) -> None:
        if native_flags:
            add_backend_flags(args, require_native, skip_build)
        steps.append(Step(name, tuple([python_exe, script, *args]), expected))

    add("01_local_audit", "run_all_checks.py", ["--out-dir", str(out_root / "local_audit")], "local_audit/audit_summary.json")

    if preset == "smoke":
        knots = ["0_1"]
        centerlines = [2048, 2304, 2560]
        ray_steps = [32, 48, 64]
        iterations = 0
        perturbations = [8e-5, 4e-5, 2e-5]
    else:
        knots = ["0_1", "3_1", "4_1", "5_2"]
        centerlines = [2048, 4096, 8192]
        ray_steps = [256, 512, 1024]
        iterations = 10
        perturbations = [4e-5, 2e-5, 1e-5]

    add(
        "02_geodesic_seed_shots",
        "run_geodesic_shooting.py",
        [
            "--knots", *knots,
            "--epsilon", "0.0019",
            "--centerline-points", str(centerlines[-1]),
            "--steps", str(ray_steps[-1]),
            "--max-iterations", str(iterations),
            "--candidate-angles", "8",
            "--out-dir", str(out_root / "geodesic_shooting"),
        ],
        "geodesic_shooting/geodesic_shooting.json",
    )
    add(
        "03_global_orbit_convergence",
        "run_orbit_convergence.py",
        [
            "--knots", *knots,
            "--epsilon", "0.0019",
            "--centerline-point-counts", *[str(v) for v in centerlines],
            "--step-counts", *[str(v) for v in ray_steps],
            "--max-iterations", str(iterations),
            "--candidate-angles", "8",
            "--out-dir", str(out_root / "orbit_convergence"),
        ],
        "orbit_convergence/orbit_convergence.json",
    )
    if preset == "smoke":
        add(
            "04_monodromy_smoke",
            "run_monodromy_smoke.py",
            ["--out-dir", str(out_root / "monodromy_smoke")],
            "monodromy_smoke/monodromy_smoke.json",
        )
    else:
        add(
            "04_monodromy_convergence",
            "run_monodromy.py",
            [
                "--knots", *knots,
                "--epsilon", "0.0019",
                "--centerline-point-counts", *[str(v) for v in centerlines],
                "--step-counts", *[str(v) for v in ray_steps],
                "--perturbation-scales", *[str(v) for v in perturbations],
                "--max-iterations", str(iterations),
                "--candidate-angles", "8",
                "--out-dir", str(out_root / "monodromy"),
            ],
            "monodromy/monodromy.json",
        )
    return steps


def run_step(step: Step, *, cwd: Path, log_path: Path) -> tuple[int, float]:
    start = time.perf_counter()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        header = f"[{utc_now()}] COMMAND: {command_text(step.arguments)}\n"
        print(header.rstrip()); log.write(header); log.flush()
        process = subprocess.Popen(
            list(step.arguments), cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end=""); log.write(line)
        rc = process.wait()
        duration = time.perf_counter() - start
        footer = f"\n[{utc_now()}] EXIT_CODE={rc} DURATION_SECONDS={duration:.3f}\n"
        print(footer.rstrip()); log.write(footer)
    return rc, duration


def create_archive(out_root: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temp = archive_path.with_suffix(archive_path.suffix + ".tmp")
    temp.unlink(missing_ok=True); archive_path.unlink(missing_ok=True)
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for path in sorted(out_root.rglob("*")):
            if path.is_file():
                zf.write(path, (Path(out_root.name) / path.relative_to(out_root)).as_posix())
    temp.replace(archive_path)


def main() -> int:
    p = argparse.ArgumentParser(description="Run the v0.5.0 global Fermat shooting and monodromy campaign.")
    p.add_argument("--preset", choices=("full", "smoke"), default="full")
    p.add_argument("--out-root", default="v0.5.0_global_orbit_output")
    p.add_argument("--archive", default="SST_fermat_pybind_research_v0.5.0_global_orbit_results.zip")
    p.add_argument("--python", dest="python_exe", default=sys.executable)
    p.add_argument("--require-native", action="store_true")
    p.add_argument("--skip-build", action="store_true")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--keep-going", action="store_true")
    p.add_argument("--no-zip", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    root = Path(__file__).resolve().parent
    out = Path(a.out_root); out = out if out.is_absolute() else (root / out).resolve()
    archive = Path(a.archive); archive = archive if archive.is_absolute() else (root / archive).resolve()
    if a.overwrite:
        shutil.rmtree(out, ignore_errors=True); archive.unlink(missing_ok=True)
    elif out.exists() and any(out.iterdir()) and not a.resume:
        raise SystemExit(f"output root already contains files: {out}\nUse --resume or --overwrite.")
    out.mkdir(parents=True, exist_ok=True); logs = out / "logs"; logs.mkdir(exist_ok=True)
    steps = campaign_steps(a.python_exe, out, preset=a.preset, require_native=a.require_native, skip_build=a.skip_build)
    env = {
        "package_version": __version__, "preset": a.preset, "project_root": str(root),
        "output_root": str(out), "archive": str(archive), "python_executable": a.python_exe,
        "python_version": sys.version, "platform": platform.platform(), "require_native": a.require_native,
        "started_utc": utc_now(),
    }
    write_json(out / "environment.json", env)
    (out / "campaign_commands.txt").write_text("\n".join(command_text(s.arguments) for s in steps) + "\n", encoding="utf-8")
    manifest = {
        "schema": "sst.fermat.global-orbit-campaign-manifest.v0.5.0",
        "package_version": __version__, "preset": a.preset, "started_utc": env["started_utc"],
        "completed_utc": None, "status": "RUNNING", "steps": [],
        "global_closed_orbit_certified": False, "monodromy_certified": False, "qsm_certified": False,
    }
    write_json(out / "campaign_manifest.json", manifest)
    if a.dry_run:
        for s in steps: print(f"{s.name}: {command_text(s.arguments)}")
        manifest["status"] = "DRY_RUN"; manifest["completed_utc"] = utc_now(); write_json(out / "campaign_manifest.json", manifest); return 0

    failed = False
    for step in steps:
        marker = logs / f"{step.name}.success.json"
        expected = out / step.expected_relative_output
        if a.resume and marker.exists() and expected.exists():
            record = json.loads(marker.read_text(encoding="utf-8")); record["resume_action"] = "SKIPPED_ALREADY_SUCCESSFUL"
            manifest["steps"].append(record); write_json(out / "campaign_manifest.json", manifest); print(f"[resume] {step.name}: skipped"); continue
        rc, duration = run_step(step, cwd=root, log_path=logs / f"{step.name}.log")
        success = rc == 0 and expected.exists()
        record = {
            "name": step.name, "command": list(step.arguments), "command_text": command_text(step.arguments),
            "completed_utc": utc_now(), "duration_seconds": duration, "exit_code": rc,
            "expected_output": str(expected), "expected_output_exists": expected.exists(),
            "status": "SUCCESS" if success else "FAILED", "log": str(logs / f"{step.name}.log"),
        }
        manifest["steps"].append(record); write_json(out / "campaign_manifest.json", manifest)
        if success: write_json(marker, record)
        else:
            failed = True
            if not a.keep_going: break

    manifest["completed_utc"] = utc_now(); manifest["status"] = "FAILED_OR_PARTIAL" if failed else "SUCCESS"
    # Read final scientific gates without converting a successful computation into a positive physics result.
    orbit_file = out / "orbit_convergence" / "orbit_convergence.json"
    mono_file = (out / "monodromy" / "monodromy.json") if a.preset == "full" else (out / "monodromy_smoke" / "monodromy_smoke.json")
    if orbit_file.exists():
        data = json.loads(orbit_file.read_text(encoding="utf-8")); manifest["global_closed_orbit_certified"] = bool(data.get("all_requested_knots_certified"))
    if mono_file.exists():
        data = json.loads(mono_file.read_text(encoding="utf-8")); manifest["monodromy_certified"] = bool(data.get("all_requested_monodromies_certified", data.get("monodromy_certified", False)))
    write_json(out / "campaign_manifest.json", manifest)
    write_json(out / "campaign_summary.json", {
        "package_version": __version__, "preset": a.preset, "status": manifest["status"],
        "successful_step_count": sum(r["status"] == "SUCCESS" for r in manifest["steps"]),
        "failed_step_count": sum(r["status"] == "FAILED" for r in manifest["steps"]),
        "global_closed_orbit_certified": manifest["global_closed_orbit_certified"],
        "monodromy_certified": manifest["monodromy_certified"], "qsm_certified": False,
    })
    if not a.no_zip:
        print(f"Creating results archive: {archive}"); create_archive(out, archive)
        digest = sha256_file(archive); archive.with_suffix(archive.suffix + ".sha256").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
        print(f"Archive SHA-256: {digest}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
