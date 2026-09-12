"""Sequential paper-upgrade run_all orchestrator."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

WB = Path(__file__).resolve().parents[1]

# Prefer VS 2022 Community/BuildTools vcvars so native pybind builds find cl.exe.
_VCVARS_CANDIDATES = [
    Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"),
    Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
    Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
]


def find_vcvars() -> Path | None:
    for p in _VCVARS_CANDIDATES:
        if p.is_file():
            return p
    return None


def apply_vcvars_env() -> bool:
    """Merge MSVC/BuildTools environment into this process (needed for cl.exe)."""
    vcvars = find_vcvars()
    if vcvars is None:
        return False
    # Capture env after vcvars; avoid relying on nested cmd inheritance alone.
    probe = subprocess.run(
        f'cmd.exe /c ""{vcvars}" && set"',
        shell=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        print(f"WARN: vcvars failed rc={probe.returncode}: {probe.stderr[:400]}", flush=True)
        return False
    for line in probe.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        # Skip cmd metadata noise
        if not key or key.startswith("!") or key.lower() in {"prompt", "cd"}:
            continue
        os.environ[key] = val
    cl = shutil.which("cl")
    # Force setuptools/distutils to honor the vcvars-selected toolchain.
    os.environ["DISTUTILS_USE_SDK"] = "1"
    os.environ["MSSdk"] = "1"
    # Prefer MSVC over stray MinGW (e.g. Strawberry Perl) on PATH.
    os.environ["CC"] = "cl"
    os.environ["CXX"] = "cl"
    print(f"MSVC env applied; cl={cl}", flush=True)
    return cl is not None


PACKS = [
    ("D006", WB / "01_research/D_benchmarks/D006_minimal_falsification_harness/D006-v0.4.0"),
    ("A037", WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1"),
    ("A034", WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1"),
    ("C006", WB / "01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.0"),
    ("A029", WB / "01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0"),
    ("A035", WB / "01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0"),
    ("A008", WB / "01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0"),
    ("A030", WB / "01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0"),
    ("A023", WB / "01_research/A_falsifiers/A023_multitopology_rpo_floquet/A023-v0.5.0"),
    ("A031", WB / "01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0"),
    ("A038", WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0"),
    ("A021", WB / "01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0"),
    ("A024", WB / "01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control"),
    ("A025", WB / "01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control"),
    ("A016", WB / "01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control"),
]


def has_done_markers(pack: Path) -> bool:
    for p in pack.glob("outputs/*/stages/*.done"):
        return True
    return False


def main() -> int:
    args = sys.argv[1:]
    continue_on_fail = False
    if "--continue-on-fail" in args:
        continue_on_fail = True
        args = [a for a in args if a != "--continue-on-fail"]
    only = args  # optional filter of family ids
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log = WB / "10_docs" / "migration" / f"paper_upgrade_run_log_{stamp}.md"
    # append to latest log if SST_RUN_LOG set
    env_log = os.environ.get("SST_RUN_LOG", "").strip()
    if env_log:
        log = Path(env_log)
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.is_file():
        lines = [
            f"# Paper-upgrade run log {stamp}",
            "",
            "Reuse policy: `/resume` when `outputs/*/stages/*.done` exists.",
            "",
        ]
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"LOG {log}")

    msvc_ok = apply_vcvars_env()
    if not msvc_ok:
        print("WARN: MSVC toolchain not on PATH after vcvars; native packs may fail", flush=True)

    failures: list[str] = []
    for fam, pack in PACKS:
        if only and fam not in only:
            continue
        run_all = pack / "run_all.cmd"
        if not run_all.is_file():
            msg = f"## {fam}\n\n- path: `{pack}`\n- status: SKIP missing run_all.cmd\n"
            with log.open("a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
            print(f"SKIP {fam}")
            continue
        resume = has_done_markers(pack)
        # Prefer SST_RESUME env over argv /resume so packs that forward %* to CLIs
        # (A035, A021, …) do not see an unrecognized /resume flag.
        env = os.environ.copy()
        cmd_args: list[str] = []
        if resume:
            env["SST_RESUME"] = "1"
        start = time.time()
        start_s = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"START {fam} resume={resume} cwd={pack}", flush=True)
        proc = subprocess.run(
            ["cmd", "/c", "run_all.cmd", *cmd_args],
            cwd=str(pack),
            capture_output=False,
            env=env,
        )
        elapsed = time.time() - start
        end_s = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cert = None
        for cand in pack.glob("outputs/*/paper_upgrade/certificate.json"):
            cert = cand
            break
        entry = (
            f"## {fam}\n\n"
            f"- path: `{pack.relative_to(WB).as_posix()}`\n"
            f"- resume: `{resume}`\n"
            f"- start: {start_s}\n"
            f"- end: {end_s}\n"
            f"- elapsed_s: {elapsed:.1f}\n"
            f"- exit_code: {proc.returncode}\n"
            f"- cert: `{cert.relative_to(WB).as_posix() if cert else 'n/a'}`\n"
        )
        with log.open("a", encoding="utf-8") as fh:
            fh.write(entry + "\n")
        print(f"END {fam} rc={proc.returncode} elapsed={elapsed:.1f}s", flush=True)
        if proc.returncode != 0:
            failures.append(fam)
            note = f"**Failure on {fam}** (continue_on_fail={continue_on_fail}).\n"
            with log.open("a", encoding="utf-8") as fh:
                fh.write(note + "\n")
            if not continue_on_fail:
                print(f"STOP on failure {fam}", flush=True)
                return proc.returncode
    with log.open("a", encoding="utf-8") as fh:
        if failures:
            fh.write(f"**Completed with failures: {', '.join(failures)}.**\n")
        else:
            fh.write("**All requested packs completed.**\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
