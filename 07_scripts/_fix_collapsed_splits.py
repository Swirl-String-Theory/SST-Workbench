"""Re-split seven containers whose SP06 rows collapsed into one destination.

Each of these was recorded as N path_map rows sharing the *container* as old_path with
N different destinations. The first row moved the whole tree into its own destination
and the rest were skipped as missing, so 16 catalog families were never created and
their content sits inside a sibling.

This generates child-granular rows sourced from where the content actually is now
(inside the winning family) and points each child at the family it belongs to.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"

RESEARCH = "01_research"
A = f"{RESEARCH}/A_falsifiers"
B = f"{RESEARCH}/B_closures"
C = f"{RESEARCH}/C_dynamics"

# winner directory -> list of (child name prefix, destination family, catalog_id)
# Children matching no prefix stay where they are.
REGROUP: dict[str, list[tuple[str, str, str]]] = {
    f"{A}/A018_einstein_blind": [
        ("Einstein_SST_Emergent_Metric_", f"{A}/A017_einstein_emergent_metric_poisson", "A017"),
    ],
    f"{A}/A034_qhp_stability_landscape": [
        ("SST_KnotPlot_QHP_Sweep_Generator", "04_tools/A_geometry/A003_knotplot_qhp_sweep_generator", "A003"),
    ],
    f"{A}/A024_threaded_hole_separatrix": [
        ("SST_Local_Thread_Texture_", f"{A}/A025_local_thread_texture_boost", "A025"),
    ],
    f"{A}/A021_trefoil_lobe_self_confinement": [
        ("SST_MultiTopology_", f"{A}/A023_multitopology_rpo_floquet", "A023"),
        ("SST_Adaptive_Period_", f"{A}/A031_adaptive_period_rpo_floquet", "A031"),
    ],
    f"{B}/B003_planck_routes_a_to_d_equivalence": [
        ("SST_v0_8_19_Planck_Routes_v3", f"{B}/B004_planck_routes_v3_preregistered", "B004"),
        ("SST_v0_8_19_RouteA_", f"{A}/A001_route_a_parallel_derivation_falsification", "A001"),
        ("sst_torsion_impedance", f"{C}/C004_torsion_impedance", "C004"),
        ("sst_nonfit_prediction_harness", f"{A}/A002_nonfit_prediction_routes_control", "A002"),
    ],
    "05_apps/A002_coil_gui": [
        ("vortexring-lab", "05_apps/A003_vortexlab", "A003"),
        ("vortexlab-modular", "05_apps/A003_vortexlab", "A003"),
        ("SST_Math_Lab", "05_apps/A004_math_lab", "A004"),
        ("additional for Vlab", f"{C}/C006_uq_twisted_vortex_ring", "C006"),
        ("images", "03_data/C_reference/C002_gui_images", "C002"),
    ],
}

# 3D splits by file extension, not by child name.
GENERATED_SUFFIXES = (".stl", ".gcode", ".obj", ".3mf")


def classify(name: str, rules: list[tuple[str, str, str]]) -> tuple[str, str] | None:
    for prefix, dest, cid in rules:
        if name.startswith(prefix):
            return dest, cid
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    new_rows: list[dict[str, str]] = []

    for winner_rel, rules in REGROUP.items():
        winner = WB / winner_rel
        if not winner.is_dir():
            print(f"  !! winner missing: {winner_rel}")
            continue
        for entry in sorted(winner.iterdir()):
            hit = classify(entry.name, rules)
            if hit is None:
                continue
            dest, cid = hit
            domain, letter = dest.split("/")[0], dest.split("/")[1]
            new_rows.append({
                "old_path": f"{winner_rel}/{entry.name}",
                "new_path": f"{dest}/{entry.name}",
                "domain": domain,
                "letter": letter if letter.startswith(("A_", "B_", "C_", "D_", "E_", "F_")) else "",
                "catalog_id": cid,
                "kind": "code",
                "phase": "SP06",
                "junction": "no",
                "status": "pending",
                "note": f"re-split from {winner_rel}; container row collapsed the tree",
            })

    # 3D: generated geometry out of the tool family.
    tool3d = WB / "04_tools/C_fabrication/C001_3d_models"
    if tool3d.is_dir():
        for path in sorted(tool3d.rglob("*")):
            if path.is_file() and path.suffix.lower() in GENERATED_SUFFIXES:
                rel = path.relative_to(tool3d).as_posix()
                new_rows.append({
                    "old_path": f"04_tools/C_fabrication/C001_3d_models/{rel}",
                    "new_path": f"03_data/D_generated/D001_3d_exports/{rel}",
                    "domain": "03_data", "letter": "D_generated",
                    "catalog_id": "D001", "kind": "output", "phase": "SP06",
                    "junction": "no", "status": "pending",
                    "note": "generated geometry split out of the 3D tool family",
                })

    by_dest: dict[str, int] = {}
    for r in new_rows:
        by_dest[r["catalog_id"]] = by_dest.get(r["catalog_id"], 0) + 1
    print("re-split rows per catalog id:")
    for cid, n in sorted(by_dest.items()):
        print(f"  {cid}: {n}")
    print(f"total new rows: {len(new_rows)}")

    if args.apply:
        with PM.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows + new_rows)
        print(f"\nWROTE {PM}")
    else:
        print("\n(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
