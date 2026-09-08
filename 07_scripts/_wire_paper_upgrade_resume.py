"""Inject resume/heartbeat bootstrap into patched run_all.cmd files."""

from __future__ import annotations

import re
from pathlib import Path

WB = Path(__file__).resolve().parents[1]

FAMILIES: list[tuple[str, str, str, Path]] = [
    ("D006", "basic", "outputs\\basic", WB / "01_research/D_benchmarks/D006_minimal_falsification_harness/D006-v0.4.0/run_all.cmd"),
    ("C006", "quick", "outputs\\quick", WB / "01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.0/run_all.cmd"),
    ("A037", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.0/run_all.cmd"),
    ("A034", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.0/run_all.cmd"),
    ("A029", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0/run_all.cmd"),
    ("A030", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0/run_all.cmd"),
    ("A023", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A023_multitopology_rpo_floquet/A023-v0.5.0/run_all.cmd"),
    ("A031", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0/run_all.cmd"),
    ("A035", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0/run_all.cmd"),
    ("A008", "quick", "outputs\\quick", WB / "01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0/run_all.cmd"),
    ("A038", "basic", "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.3-outputs\\basic", WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0/run_all.cmd"),
    ("A021", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0/run_all.cmd"),
    ("A024", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control/run_all.cmd"),
    ("A025", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control/run_all.cmd"),
    ("A016", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control/run_all.cmd"),
    ("A036", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A036_scii_intrinsic_modal_phase_clock/A036-v0.1.1/run_all.cmd"),
    ("A039", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A039_sciib_frozen_modal_pair_phase_clock/A039-v0.1.1/run_all.cmd"),
    ("A040", "basic", "outputs\\basic", WB / "01_research/A_falsifiers/A040_sciii_koopman_dmd_phase_clock/A040-v0.1.0/run_all.cmd"),
]

MARKER = "rem --- paper-upgrade resume/heartbeat (PU01b) ---"


def bootstrap(family: str, tier: str, out: str) -> str:
    # One-liner which-wb (no labels; safe inside run_all.cmd)
    which = (
        'python -c "from pathlib import Path;import sys;p=Path.cwd().resolve();'
        "cs=[p,*p.parents];"
        "ok=[c for c in cs if (c/'07_scripts'/'paper_upgrade_runtime.py').is_file()];"
        "print(ok[0] if ok else '');"
        'sys.exit(0 if ok else 2)"'
    )
    lines = [
        MARKER,
        f'set "PU_FAMILY={family}"',
        f'set "PU_TIER={tier}"',
        f'set "PU_OUT={out}"',
        'echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"',
        'echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"',
        f'for /f "delims=" %%W in (\'{which}\') do set "PU_WB=%%W"',
        'if not defined PU_WB (echo [paper-upgrade] ERROR: workbench root not found & exit /b 2)',
        'set "PU_RESUME_FLAG="',
        'if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"',
        'python "%PU_WB%\\07_scripts\\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG% || exit /b 1',
        "",
    ]
    return "\r\n".join(lines)


def stage_wrap_calls(text: str) -> str:
    """Wrap simple `call foo.cmd ... || exit /b 1` lines as resumable stages."""

    def repl(m: re.Match[str]) -> str:
        indent = m.group(1)
        cmd = m.group(2).strip()
        rest = (m.group(3) or "").strip()
        # stage id from script basename
        base = re.split(r"[\\/ ]", cmd)[0]
        base = base.replace('"', "")
        if base.lower().startswith("run_"):
            sid = base[4:]
            if sid.lower().endswith(".cmd"):
                sid = sid[:-4]
        else:
            sid = re.sub(r"[^A-Za-z0-9_]+", "_", base)[:40]
        full = cmd if not rest else f"{cmd} {rest}"
        return (
            f'{indent}python "%PU_WB%\\07_scripts\\paper_upgrade_runtime.py" stage '
            f'--family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "{sid}" %PU_RESUME_FLAG% -- '
            f"{full} || exit /b 1\r\n"
        )

    # Only wrap calls that look like run_*.cmd and are not already staged
    pattern = re.compile(
        r'(?im)^([ \t]*)call[ \t]+((?:\"?[^\s\"]*run_[^\s\"]+\.cmd\"?)|(?:run_[^\s]+\.cmd))([^\r\n]*?)(?:\|\|[ \t]*exit[ \t]+/b[ \t]+1)?[ \t]*\r?$',
    )
    out_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if "paper_upgrade_runtime.py" in line and " stage " in line:
            out_lines.append(line)
            continue
        if "run_paper_upgrade" in line:
            out_lines.append(line)
            continue
        m = pattern.match(line.rstrip("\r\n"))
        if m:
            out_lines.append(repl(m))
        else:
            out_lines.append(line)
    return "".join(out_lines)


def patch(path: Path, family: str, tier: str, out: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        return "skip"
    pat = re.compile(
        r'(call (?:\"%~dp0)?run_paper_upgrade\.cmd\"? \|\| exit /b 1\s*\r?\n)',
        re.IGNORECASE,
    )
    m = pat.search(text)
    if not m:
        return "missing-hook"
    text2 = text[: m.end()] + bootstrap(family, tier, out) + text[m.end() :]
    text2 = stage_wrap_calls(text2)
    if 'paper_upgrade_runtime.py" finish' not in text2 and "paper_upgrade_runtime.py finish" not in text2:
        finish = (
            'python "%PU_WB%\\07_scripts\\paper_upgrade_runtime.py" finish '
            '--family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status DONE\r\n'
        )
        # Prefer append before first plain exit /b near end; else append
        matches = list(re.finditer(r"(?im)^exit /b.*$", text2))
        if matches:
            last = matches[-1]
            text2 = text2[: last.start()] + finish + text2[last.start() :]
        else:
            text2 = text2.rstrip() + "\r\n" + finish
    path.write_text(text2, encoding="utf-8", newline="\r\n")
    return "patched"


def main() -> None:
    for fam, tier, out, path in FAMILIES:
        status = patch(path, fam, tier, out)
        print(f"{fam}: {status} -> {path}")


if __name__ == "__main__":
    main()
