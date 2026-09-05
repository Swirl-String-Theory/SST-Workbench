"""Bring four family directories back in line with the frozen catalog.

SP06's repair scripts took catalog ids from the pre-freeze path_map instead of
CATALOG_v0.1.md, so the tree drifted from the plan in four places:

1. The Planck routes are ONE family with two versions in the catalog
   (B002_planck_routes_a_to_d), but landed as two families that also stole the ids
   belonging to horn_bem (B003) and route_b_rt_bem (B004). Merging them resolves both
   duplicate ids at once.
2. The QHP sweep generator belongs at E007 under pipelines - the catalog says so
   explicitly, and E_pipelines has a gap at exactly E007 - but landed under tools.
3. C006 is kelvin_floquet_workbench in the catalog. The U(q) twisted vortex ring
   experiment, added later when GUI/additional for Vlab turned out to be research
   rather than an app asset, has to move to the next free number.

Nothing is deleted; every step is a git mv.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

WB = Path(__file__).resolve().parents[1]

R = "01_research"
B = f"{R}/B_closures"
C = f"{R}/C_dynamics"
E = f"{R}/E_pipelines"
T = "04_tools/A_geometry"

#: (source, destination, why) - executed in order
MOVES: list[tuple[str, str, str]] = [
    # 1. Planck routes: two directories become two versions of one family.
    (
        f"{B}/B003_planck_routes_a_to_d_equivalence/SST_v0_8_19_Planck_Routes_A_to_D_equivalence_corrected_pack",
        f"{B}/B002_planck_routes_a_to_d/SST_v0_8_19_Planck_Routes_A_to_D_equivalence_corrected_pack",
        "catalog: B002 planck_routes_a_to_d, 2 versions",
    ),
    (
        f"{B}/B004_planck_routes_v3_preregistered/SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack",
        f"{B}/B002_planck_routes_a_to_d/SST_v0_8_19_Planck_Routes_v3_preregistered_all_inclusive_pack",
        "catalog: the v3 pack is the second version of B002",
    ),
    # 2. QHP sweep generator belongs under pipelines.
    (
        f"{T}/A003_knotplot_qhp_sweep_generator",
        f"{E}/E007_knotplot_qhp_sweep_generator",
        "catalog: 'QHP Sweep Generator is E007 under pipelines'",
    ),
    # 3. U(q) experiment takes the next free C id.
    (
        f"{C}/C006_uq_twisted_vortex_ring",
        f"{C}/C007_uq_twisted_vortex_ring",
        "C006 is kelvin_floquet_workbench in the catalog",
    ),
]


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=WB, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    errors = 0
    for src_rel, dst_rel, why in MOVES:
        src, dst = WB / src_rel, WB / dst_rel
        if not src.exists():
            print(f"  SKIP  {src_rel}  (not on disk)")
            continue
        if dst.exists():
            print(f"  SKIP  {dst_rel}  (destination already exists)")
            continue
        print(f"  MOVE  {src_rel}\n     -> {dst_rel}\n        ({why})")
        if not args.apply:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        proc = git("mv", src_rel, dst_rel)
        if proc.returncode != 0:
            print(f"  ERROR {(proc.stderr or proc.stdout).strip()}")
            errors += 1

    if args.apply:
        # Drop the now-empty family shells left behind by the Planck merge.
        for shell in (
            WB / f"{B}/B003_planck_routes_a_to_d_equivalence",
            WB / f"{B}/B004_planck_routes_v3_preregistered",
        ):
            if shell.is_dir() and not any(shell.iterdir()):
                shell.rmdir()
                print(f"  rmdir empty shell {shell.relative_to(WB).as_posix()}")

    print("\n(dry run)" if not args.apply else f"\ndone, errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
