#!/usr/bin/env python3
"""Lift to_be_processed packs into Workbench-root research folders + vortexring inbox.

Usage:
  python scripts/reorg_to_be_processed.py --dry-run
  python scripts/reorg_to_be_processed.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
SRC = WB / "to_be_processed"

# (source relative to to_be_processed, destination absolute under WB)
DIR_MOVES: list[tuple[str, str]] = [
    # chi_phase children -> SST_chi_phase_research/<name>
    *(
        (f"chi_phase/{name}", f"SST_chi_phase_research/{name}")
        for name in (
            "sst_chi_phase_package_v10B1",
            "sst_chi_phase_package_v11B0",
            "sst_chi_phase_package_v12B0",
            "sst_chi_phase_package_v13B0",
            "sst_chi_phase_package_v14B0",
            "sst_chi_phase_package_v15B0",
            "sst_chi_phase_package_v16B0",
            "sstcore_chiE_local0",
            "sstcore_chiE_local_v4",
            "sstcore_chiE_local_v5",
            "sstcore_chiE_local_v6",
            "sstcore_chiE_local_v7",
        )
    ),
    ("sst_horn_dirichlet_package", "SST_horn_bem_research/sst_horn_dirichlet_package"),
    ("sst_horn_neumann_bem_package", "SST_horn_bem_research/sst_horn_neumann_bem_package"),
    (
        "sst_horn_neumann_bem_all_audits",
        "SST_horn_bem_research/sst_horn_neumann_bem_all_audits",
    ),
    (
        "SST_v0_8_19_Planck_Routes_A_to_D_equivalence_corrected_pack",
        "SST_v0_8_19_routes_research/SST_v0_8_19_Planck_Routes_A_to_D_equivalence_corrected_pack",
    ),
    (
        "SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack",
        "SST_v0_8_19_routes_research/SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack",
    ),
    (
        "SST_v0_8_19_RouteA_parallel_derivation_falsification_pack",
        "SST_v0_8_19_routes_research/SST_v0_8_19_RouteA_parallel_derivation_falsification_pack",
    ),
    (
        "sst_nonfit_prediction_harness_v0_8_19",
        "SST_v0_8_19_routes_research/sst_nonfit_prediction_harness_v0_8_19",
    ),
    (
        "sst_torsion_impedance_pybind11_v0.8.19_autobuild",
        "SST_v0_8_19_routes_research/sst_torsion_impedance_pybind11_v0.8.19_autobuild",
    ),
    ("ssdl_audit", "SST_ssdl_audit_research/ssdl_audit"),
    ("ssdl_audit_v0_2", "SST_ssdl_audit_research/ssdl_audit_v0_2"),
    (
        "SST_dark_knot_rayleigh_harness",
        "SST_dark_knot_rayleigh_research/SST_dark_knot_rayleigh_harness",
    ),
    (
        "sst_ideal_trefoil_biot_package_v2",
        "SST_ideal_trefoil_biot_research/sst_ideal_trefoil_biot_package_v2",
    ),
    ("sst_trefoil_bs", "SST_ideal_trefoil_biot_research/sst_trefoil_bs"),
    (
        "sst_3d_collider_robust",
        "SST_ideal_trefoil_biot_research/sst_3d_collider_robust",
    ),
    (
        "SST_fermat_pybind_research_v0.1",
        "SST_fermat_pybind_research/SST_fermat_pybind_research_v0.1",
    ),
    (
        "routeI_heat_guard_patch_bundle_v0_8_19",
        "SST_Route_I_relative_entropy_PoC/routeI_heat_guard_patch_bundle_v0_8_19",
    ),
]

VORTEX_INBOX = "GUI/vortexring-lab/inbox_from_to_be_processed"

STUB = """# to_be_processed (relocated)

Contents were lifted to Workbench-root research folders and `GUI/vortexring-lab/`.

| Former | New location |
|--------|--------------|
| `chi_phase/*` | `SST_chi_phase_research/` |
| horn BEM packs | `SST_horn_bem_research/` |
| v0.8.19 Planck/Route packs | `SST_v0_8_19_routes_research/` |
| `ssdl_audit*` | `SST_ssdl_audit_research/` |
| dark-knot Rayleigh harness | `SST_dark_knot_rayleigh_research/` |
| trefoil biot / BS / collider | `SST_ideal_trefoil_biot_research/` |
| `SST_fermat_pybind_research_v0.1` | `SST_fermat_pybind_research/SST_fermat_pybind_research_v0.1/` |
| `routeI_heat_guard_patch_bundle_v0_8_19` | `SST_Route_I_relative_entropy_PoC/` |
| vortexring/gem HTML+JS+builders | `GUI/vortexring-lab/inbox_from_to_be_processed/` |
"""


def resolve_dir_moves() -> list[tuple[Path, Path]]:
    out: list[tuple[Path, Path]] = []
    for src_rel, dst_rel in DIR_MOVES:
        out.append((SRC / src_rel, WB / dst_rel))
    return out


def list_vortex_files() -> list[Path]:
    """Loose files at to_be_processed root (not directories)."""
    if not SRC.is_dir():
        return []
    return sorted([p for p in SRC.iterdir() if p.is_file()], key=lambda p: p.name.lower())


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path)
    except OSError:
        r = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
            capture_output=True,
            text=True,
        )
        if path.exists():
            raise RuntimeError(f"Failed to remove {path}: {r.stderr}")


def _safe(msg: str) -> str:
    return msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
        sys.stdout.encoding or "utf-8", errors="replace"
    )


def move_path(src: Path, dst: Path, dry_run: bool) -> None:
    if not src.exists():
        print(_safe(f"MISS {src.relative_to(WB)}"))
        return
    if dst.exists():
        raise FileExistsError(f"Destination exists: {dst.relative_to(WB)}")
    if dry_run:
        print(_safe(f"DRY  {src.relative_to(WB)} -> {dst.relative_to(WB)}"))
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print(_safe(f"MOVE {src.relative_to(WB)} -> {dst.relative_to(WB)}"))


def reorg(dry_run: bool) -> int:
    if not SRC.is_dir():
        print(f"ERROR: missing {SRC}", file=sys.stderr)
        return 1

    moves = resolve_dir_moves()
    for src, dst in moves:
        move_path(src, dst, dry_run)

    inbox = WB / VORTEX_INBOX
    for src in list_vortex_files():
        move_path(src, inbox / src.name, dry_run)

    # remove empty chi_phase + __pycache__
    for leftover in (SRC / "chi_phase", SRC / "__pycache__"):
        if dry_run:
            if leftover.exists():
                print(f"DRY RMDIR {leftover.relative_to(WB)}")
        else:
            if leftover.exists():
                force_rmtree(leftover)
                print(f"RMDIR {leftover.relative_to(WB)}")

    if dry_run:
        print("DRY would write to_be_processed/README.md stub")
        remaining = [p.name for p in SRC.iterdir()] if SRC.exists() else []
        print(f"DRY remaining after simulated moves would still include sources; apply for real")
        print(f"planned dir moves={len(moves)} vortex files={len(list_vortex_files())}")
        return 0

    # any leftovers?
    leftovers = [p for p in SRC.iterdir()] if SRC.exists() else []
    if leftovers:
        print("WARN leftovers:", [p.name for p in leftovers])

    SRC.mkdir(parents=True, exist_ok=True)
    (SRC / "README.md").write_text(STUB, encoding="utf-8")
    print("STUB to_be_processed/README.md")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return reorg(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
