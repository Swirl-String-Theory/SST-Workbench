#!/usr/bin/env python3
"""Move experiments/derive_constants into fermat-style Workbench research roots.

Idempotent where possible: skips moves whose destination already exists with the
same basename. Writes MOVE_DERIVE_CONSTANTS_MANIFEST.md at Workbench root.

Usage:
  python scripts/reorg_derive_constants.py --dry-run
  python scripts/reorg_derive_constants.py
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
SRC = WB / "experiments" / "derive_constants"

DEST = {
    "derive": WB / "SST_derive_constants_research",
    "routeB": WB / "SST_routeB_RT_bem_research",
    "coil": WB / "SST_Coil_DigitalTwin_research",
    "lab": WB / "SST_CoilLab_research",
    "bridge": WB / "SST_contra_swirl_bridge_research",
    "fs": WB / "SST_fs_attachment_audit_research",
    "tf": WB / "SST_timefield_spectral_v06_research",
}

STUBS_TO_DROP = {
    "_mounttest.txt",
    "_patch.py",
    "_patch2.py",
    "_tmp_head.py",
}

TIMEFIELD_PREFIXES = (
    "audit_result",
    "canon_",
    "channel_metrics",
    "enantiomer_",
    "fig4_",
    "fit_parameters",
    "fitted_predictions",
    "observed_vs_",
    "pairwise_",
    "residuals_vs_",
    "signal_vs_",
    "spectral_",
    "sst_feature_bank",
    "sst_timefield_",
    "suite_manifest",
    "supplement_",
    "synthetic_demo_data",
    "timefield_",
    "v03_spectral_",
    "v06_",
)

FS_PREFIXES = (
    "README_MAXHR_unified_attachment_audit",
    "attachment_",
    "compensated_attachment_",
    "framed_helicity_",
    "gear_locked_attachment_",
    "trefoil_patch_smoke_",
)

GEO_NAMES = {
    "30cm_axle.stl",
    "trefoil_core_helix_blender_script.py",
    "trefoil_core_plus_blade_connector_v4.1.stl",
    "trefoil_core_plus_blade_connector_v4.2.stl",
    "trefoil_core_plus_blade_connector_v4.stl",
    "trefoil_core_plus_blade_connector_v5_16_turns.stl",
    "trefoil_core_v5_16_turns.stl",
    "triple_gear_part_1.stl",
    "triple_gear_part_2.stl",
    "triple_gear_part_3.stl",
    "triple_gear_solid_with_mark.stl",
}

KNOT_SHARED = {
    "ideal.txt",
    "ideal_knot_index.md",
    "knots.zip",
    "knots_source_inventory.csv",
    "link_kernel.cpp",
}

BRIDGE_SCRIPT_RE = re.compile(
    r"^sst_contra_swirl_bridge_test(?:_v(?P<ver>[\d_]+(?:_[a-z0-9_]+)?))?\.py$"
)

VERSION_TOKEN_RE = re.compile(
    r"(?:^|_)v(?P<maj>\d+)(?:_(?P<min>\d+))?(?:_(?P<rest>.+))?$"
)


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    total = 0
    for _, _, files in os.walk(path):
        total += len(files)
    return total


def ensure_parent(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)


def move_path(src: Path, dst: Path, moves: list[tuple[str, str, int]], dry_run: bool) -> None:
    if not src.exists():
        return
    n = count_files(src)
    rel_src = str(src.relative_to(WB)).replace("\\", "/")
    rel_dst = str(dst.relative_to(WB)).replace("\\", "/")
    if dst.exists():
        # Resume-safe: already moved on a prior partial run.
        print(f"SKIP {rel_src}  ->  {rel_dst}  (dest exists)")
        return
    moves.append((rel_src, rel_dst, n))
    if dry_run:
        print(f"DRY  {rel_src}  ->  {rel_dst}  ({n} files)")
        return
    ensure_parent(dst)
    shutil.move(str(src), str(dst))
    print(f"MOVE {rel_src}  ->  {rel_dst}  ({n} files)")


def drop_file(src: Path, drops: list[str], dry_run: bool) -> None:
    if not src.exists() or not src.is_file():
        return
    rel = str(src.relative_to(WB)).replace("\\", "/")
    drops.append(rel)
    if dry_run:
        print(f"DROP {rel}")
        return
    src.unlink()
    print(f"DROP {rel}")


def find_schrodinger_dir(routeb: Path) -> Path | None:
    if not routeb.is_dir():
        return None
    for child in routeb.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if "Gate" in name and ("Schr" in name or "chro" in name.lower() or "ödinger" in name):
            return child
        # mojibake / encoding variants
        if "Gate Constants Audit" in name:
            return child
    return None


def version_folder_for_bem_script(name: str) -> str | None:
    """Map BEM_Route filename to SST_routeB_RT_bem_research_vX folder name."""
    if name.startswith("routeB_RT_bem_stecklov"):
        return "SST_routeB_RT_bem_research_stecklov"
    m = re.match(r"routeB_RT_bem_v(\d+)(?:_(\d+))?(?:_.*)?\.(?:py|md)$", name)
    if m:
        maj, minor = m.group(1), m.group(2)
        if minor is not None:
            return f"SST_routeB_RT_bem_research_v{maj}_{minor}"
        return f"SST_routeB_RT_bem_research_v{maj}"
    m = re.match(r"README_routeB_RT_bem_v(\d+)(?:_(\d+))?(?:_.*)?\.md$", name)
    if m:
        maj, minor = m.group(1), m.group(2)
        if minor is not None:
            return f"SST_routeB_RT_bem_research_v{maj}_{minor}"
        return f"SST_routeB_RT_bem_research_v{maj}"
    m = re.match(r"README_routeB_RT_bem_stecklov.*", name)
    if m:
        return "SST_routeB_RT_bem_research_stecklov"
    return None


def output_version_key(dirname: str) -> str | None:
    """Return version folder name for an outputs_* directory, or 'legacy'."""
    if dirname.startswith("outputs_routeB_BEM_v"):
        rest = dirname[len("outputs_routeB_BEM_v") :]
        # v9 _demo has a space
        rest = rest.lstrip()
        m = re.match(r"(\d+)(?:_(\d+))?", rest)
        if not m:
            return "legacy"
        maj = m.group(1)
        # stage / demo suffixes stay under major version
        return f"SST_routeB_RT_bem_research_v{maj}"
    if dirname in {"outputs_v15", "outputs_v16", "outputs_v17"}:
        return f"SST_routeB_RT_bem_research_v{dirname.split('_v')[-1]}"
    return "legacy"


def bridge_version_dir(script_name: str) -> str:
    m = BRIDGE_SCRIPT_RE.match(script_name)
    if not m:
        return "SST_contra_swirl_bridge_research_v0"
    ver = m.group("ver")
    if not ver:
        return "SST_contra_swirl_bridge_research_v0"
    # v0_2 / v0_4_spectral_epr / v0_6_timefield_supplement_audit
    # Keep short folder: v0_2, v0_4, v0_6 (and v0_3)
    parts = ver.split("_")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        short = f"{parts[0]}_{parts[1]}"
    elif parts[0].isdigit():
        short = parts[0]
    else:
        short = ver
    return f"SST_contra_swirl_bridge_research_v{short}"


def is_timefield_name(name: str) -> bool:
    return any(name.startswith(p) for p in TIMEFIELD_PREFIXES)


def is_fs_name(name: str) -> bool:
    return any(name.startswith(p) for p in FS_PREFIXES)


def reorg(dry_run: bool) -> int:
    if not SRC.is_dir():
        print(f"ERROR: source missing: {SRC}", file=sys.stderr)
        return 1

    moves: list[tuple[str, str, int]] = []
    drops: list[str] = []
    baseline = count_files(SRC)
    print(f"Baseline source files: {baseline}")

    bem = SRC / "bem"
    routeb = SRC / "routeB_RT_bem"
    code = SRC / "code"
    bem_root = bem / "root"
    bem_route = bem_root / "BEM_Route"
    bem_outputs = bem / "outputs"

    # --- 1) CoilLab ---
    for name in ("SST_CoilLab_v1", "SST_CoilLab_v2_work"):
        move_path(bem / "coillab" / name, DEST["lab"] / name, moves, dry_run)

    # --- 2) Coil DigitalTwin ---
    if routeb.is_dir():
        for child in sorted(routeb.iterdir()):
            if child.is_dir() and child.name.startswith("SST_Coil_DigitalTwin_"):
                move_path(child, DEST["coil"] / child.name, moves, dry_run)
        move_path(routeb / "exports", DEST["coil"] / "exports", moves, dry_run)

    # --- 3) Bridge ---
    if bem_root.is_dir():
        for child in sorted(bem_root.iterdir()):
            if child.is_file() and child.name.startswith("sst_contra_swirl_bridge_test"):
                vdir = bridge_version_dir(child.name)
                move_path(child, DEST["bridge"] / vdir / child.name, moves, dry_run)
            elif child.is_file() and child.name == "bridge_length_response_fit.png":
                move_path(child, DEST["bridge"] / "bridge_length_response_fit.png", moves, dry_run)
    if routeb.is_dir():
        for child in sorted(routeb.iterdir()):
            if not child.is_dir():
                continue
            if child.name in {"sst_bridge_single_test", "sst_bridge_sweep_test"}:
                move_path(child, DEST["bridge"] / "results" / child.name, moves, dry_run)
            elif child.name.startswith("sst_bridge_v"):
                # sst_bridge_v0_2_results -> v0_2
                m = re.match(r"sst_bridge_v(\d+_\d+)", child.name)
                if m:
                    vdir = f"SST_contra_swirl_bridge_research_v{m.group(1)}"
                    move_path(child, DEST["bridge"] / vdir / child.name, moves, dry_run)
                else:
                    move_path(child, DEST["bridge"] / "results" / child.name, moves, dry_run)

    # --- 4) Timefield / spectral v06 ---
    if bem_root.is_dir():
        for child in sorted(bem_root.iterdir()):
            if child.is_file() and is_timefield_name(child.name):
                move_path(child, DEST["tf"] / child.name, moves, dry_run)
        # CASTLE / Science supplement data nearest to timefield
        move_path(bem_root / "externe_data", DEST["tf"] / "externe_data", moves, dry_run)
    if routeb.is_dir():
        move_path(routeb / "timefield_crops", DEST["tf"] / "timefield_crops", moves, dry_run)

    # --- 5) FS / attachment ---
    move_path(bem_root / "fs_core", DEST["fs"] / "fs_core", moves, dry_run)
    if bem_root.is_dir():
        for child in sorted(bem_root.iterdir()):
            if child.is_file() and is_fs_name(child.name):
                move_path(child, DEST["fs"] / child.name, moves, dry_run)
            elif child.is_file() and child.name in GEO_NAMES:
                move_path(child, DEST["fs"] / "geometry" / child.name, moves, dry_run)
            elif child.is_file() and child.name in {
                "hopfion_tools.py",
                "writhe_kernel.cpp",
                "README_hopfion_pipeline.md",
            }:
                move_path(child, DEST["fs"] / "hopfion" / child.name, moves, dry_run)
    if routeb.is_dir():
        for name in (
            "unified_attachment_audit_BROAD",
            "unified_attachment_audit_full",
            "unified_trefoil_gear_audit",
            "tl33_gear_link_audit",
            "attachment_audit_out",
            "plan_demo_outputs_v18",
            "reuse_demov10",
            "results",
        ):
            move_path(routeb / name, DEST["fs"] / name, moves, dry_run)

    # Root-level hopfion / writhe duplicates
    for name in ("hopfion_tools.py", "writhe_kernel.cpp"):
        src = SRC / name
        if src.exists():
            move_path(src, DEST["fs"] / "hopfion" / f"from_derive_root_{name}", moves, dry_run)

    # --- 6) RouteB BEM research ---
    # Versioned scripts from BEM_Route
    if bem_route.is_dir():
        for child in sorted(bem_route.iterdir()):
            if not child.is_file():
                continue
            name = child.name
            vfolder = version_folder_for_bem_script(name)
            if vfolder:
                move_path(child, DEST["routeB"] / vfolder / name, moves, dry_run)
                continue
            # Suite configs -> matching major version
            if name.startswith("BEMv14") or name.startswith("README_BEMv14") or name.startswith(
                "run_bemv14"
            ):
                move_path(
                    child,
                    DEST["routeB"] / "SST_routeB_RT_bem_research_v14" / name,
                    moves,
                    dry_run,
                )
                continue
            if name.startswith("BEMv18") or name.startswith("README_BEMv18"):
                move_path(
                    child,
                    DEST["routeB"] / "SST_routeB_RT_bem_research_v18" / name,
                    moves,
                    dry_run,
                )
                continue
            if name.startswith("BEMv19") or name.startswith("README_BEMv19"):
                move_path(
                    child,
                    DEST["routeB"] / "SST_routeB_RT_bem_research_v19" / name,
                    moves,
                    dry_run,
                )
                continue
            if name in {
                "bem_scale_roles.py",
                "BEM_SCALE_ROLE_CONVENTION.md",
                "BEM_canonical_alias_map.md",
                "README_BEM_SCALE_ROLE_PATCH.md",
            }:
                move_path(child, DEST["routeB"] / "shared" / name, moves, dry_run)
                continue
            # leftover BEM_Route files
            move_path(child, DEST["routeB"] / "shared" / name, moves, dry_run)

    # Outputs
    if bem_outputs.is_dir():
        for child in sorted(bem_outputs.iterdir()):
            if not child.is_dir():
                continue
            key = output_version_key(child.name)
            if key == "legacy":
                move_path(child, DEST["routeB"] / "outputs" / "legacy" / child.name, moves, dry_run)
            else:
                move_path(child, DEST["routeB"] / key / child.name, moves, dry_run)

    # demos + knot-data
    move_path(bem / "demos", DEST["routeB"] / "demos", moves, dry_run)
    move_path(bem / "knot-data", DEST["routeB"] / "knot-data", moves, dry_run)

    # shared knot helpers + run scripts from bem/root
    if bem_root.is_dir():
        for child in sorted(bem_root.iterdir()):
            if child.is_file() and child.name in KNOT_SHARED:
                move_path(child, DEST["routeB"] / "knot-data" / child.name, moves, dry_run)
            elif child.is_file() and child.name.startswith("run_") and child.suffix in {
                ".sh",
                ".ps1",
            }:
                move_path(child, DEST["routeB"] / "shared" / child.name, moves, dry_run)
            elif child.is_file() and child.name == "README_routeB_RT_bem_v4_zeta_falsifier.zip":
                move_path(
                    child,
                    DEST["routeB"] / "SST_routeB_RT_bem_research_v4" / child.name,
                    moves,
                    dry_run,
                )
            elif child.is_file() and child.name == "BUILD.md":
                move_path(child, DEST["routeB"] / "BUILD_bem_root.md", moves, dry_run)
            elif child.is_file() and child.name == ".gitignore":
                move_path(child, DEST["routeB"] / ".gitignore", moves, dry_run)

    # --- 7) Derive constants package ---
    for name in (
        "Manuscripts",
        "figures",
        "BUILD.md",
        "README_Derive_Constants.md",
        "README_MAJOR_REVISION_STATUS.md",
        "README_alpha_cell_closure.md",
        "CHANGELOG_major_revision_claim_status.md",
        "CHANGELOG_phase_pressure_gate.md",
    ):
        move_path(SRC / name, DEST["derive"] / name, moves, dry_run)

    # code/ (drop stubs first)
    if code.is_dir():
        for stub in STUBS_TO_DROP:
            drop_file(code / stub, drops, dry_run)
        # drop __pycache__ (best-effort on Windows locks)
        pyc = code / "__pycache__"
        if pyc.is_dir():
            if dry_run:
                print(f"DROPDIR {pyc.relative_to(WB)}")
            else:
                try:
                    shutil.rmtree(pyc)
                    print(f"DROPDIR {pyc.relative_to(WB)}")
                except OSError as exc:
                    print(f"WARN skip __pycache__: {exc}")
                    aside = DEST["derive"] / "_unclassified_from_derive_constants" / "code__pycache"
                    if not aside.exists():
                        try:
                            ensure_parent(aside)
                            shutil.move(str(pyc), str(aside))
                            print(f"MOVE locked __pycache__ -> {aside.relative_to(WB)}")
                        except OSError as exc2:
                            print(f"WARN could not relocate __pycache__: {exc2}")
        move_path(code, DEST["derive"] / "code", moves, dry_run)

    # Emergent SR audits
    for src_path, dest_name in (
        (SRC / "SST_emergent_SR_foundational_audit.md", "SST_emergent_SR_foundational_audit.md"),
        (
            SRC / "SST_emergent_SR_foundational_audit (1).md",
            "SST_emergent_SR_foundational_audit_(1).md",
        ),
        (
            bem_root / "SST_emergent_SR_foundational_audit.md",
            "SST_emergent_SR_foundational_audit_bem_root.md",
        ),
    ):
        if src_path.exists():
            move_path(
                src_path,
                DEST["derive"] / "audits" / "emergent_SR" / dest_name,
                moves,
                dry_run,
            )

    # Schrödinger micropack
    if bem_root.is_dir():
        for child in sorted(bem_root.iterdir()):
            if child.is_file() and child.name.startswith("sst_schrodinger_"):
                move_path(child, DEST["derive"] / "schrodinger_gate" / child.name, moves, dry_run)
    sch = find_schrodinger_dir(routeb) if routeb.is_dir() else None
    if sch is not None:
        move_path(sch, DEST["derive"] / "schrodinger_gate" / "SST_Schrodinger_Gate_Constants_Audit", moves, dry_run)

    # Drop routeB __pycache__ (best-effort)
    if routeb.is_dir():
        pyc = routeb / "__pycache__"
        if pyc.is_dir():
            if dry_run:
                print(f"DROPDIR {pyc.relative_to(WB)}")
            else:
                try:
                    shutil.rmtree(pyc)
                    print(f"DROPDIR {pyc.relative_to(WB)}")
                except OSError as exc:
                    print(f"WARN skip __pycache__: {exc}")
                    # If locked, move aside into dest unclassified so SRC can empty
                    aside = DEST["derive"] / "_unclassified_from_derive_constants" / "routeB_RT_bem__pycache"
                    if not aside.exists():
                        try:
                            ensure_parent(aside)
                            shutil.move(str(pyc), str(aside))
                            print(f"MOVE locked __pycache__ -> {aside.relative_to(WB)}")
                        except OSError as exc2:
                            print(f"WARN could not relocate __pycache__: {exc2}")

    # Sweep any remaining files under SRC into _unclassified for visibility
    if not dry_run:
        leftovers = []
        for dirpath, dirnames, filenames in os.walk(SRC):
            # skip emptying logic dirs we'll remove
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                leftovers.append(Path(dirpath) / fn)
            for dn in list(dirnames):
                pass
        for leftover in leftovers:
            # ignore nothing — move unclassified
            rel = leftover.relative_to(SRC)
            dest = DEST["derive"] / "_unclassified_from_derive_constants" / rel
            if leftover.exists():
                move_path(leftover, dest, moves, dry_run)

        # remove empty directories under SRC
        for dirpath, dirnames, filenames in os.walk(SRC, topdown=False):
            p = Path(dirpath)
            try:
                if p != SRC and not any(p.iterdir()):
                    p.rmdir()
                    print(f"RMDIR {p.relative_to(WB)}")
            except OSError:
                pass

    # Manifest
    manifest_path = WB / "MOVE_DERIVE_CONSTANTS_MANIFEST.md"
    lines = [
        "# MOVE derive_constants -> research folders",
        "",
        f"- Source: `experiments/derive_constants/` (baseline files: {baseline})",
        f"- Dry-run: {dry_run}",
        f"- Move records: {len(moves)}",
        f"- Dropped stubs: {len(drops)}",
        "",
        "## Destinations",
        "",
    ]
    for key, path in DEST.items():
        n_after = count_files(path) if path.exists() and not dry_run else None
        label = f"{n_after} files after apply" if n_after is not None else "n/a until apply"
        lines.append(f"- `{path.name}/` ({label})")
    lines += ["", "## Moves", "", "| source | destination | files |", "|---|---|---:|"]
    for s, d, n in moves:
        lines.append(f"| `{s}` | `{d}` | {n} |")
    if drops:
        lines += ["", "## Dropped stubs", ""]
        for d in drops:
            lines.append(f"- `{d}`")
    body = "\n".join(lines) + "\n"
    if not dry_run:
        manifest_path.write_text(body, encoding="utf-8")
        print(f"Wrote {manifest_path}")
    else:
        print("--- dry-run manifest preview (not written) ---")
        print(body[:1500])
        print(f"... ({len(lines)} lines)")

    moved_files = sum(n for _, _, n in moves)
    print(f"Total files in move table: {moved_files}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return reorg(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
