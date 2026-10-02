"""Repair path_map.csv SP06 rows: child granularity, stale catalog IDs, domain nesting.

Three faults found by scripts/test_path_map.py after the A001-A042 catalog freeze:

1. Container-split rows are recorded at *container* granularity, so several rows share
   an identical new_path (139 rows, 131 unique). A move driven from this file would
   collide. Each split row must name the child directory it actually moves.
2. Three catalog_id values predate the freeze: C008, F007, F008.
3. One new_path nests a domain inside another: 01_research/04_tools/D_compute/...

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"

# container -> ordered list of (child_glob_prefix, new_path, catalog_id)
# Destinations follow CATALOG_v0.1.md as frozen 2026-09-04.
SPLITS: dict[str, list[tuple[str, str, str]]] = {
    "SST_Maxwell": [
        ("1_", "01_research/A_falsifiers/A011_maxwell_1_kinetic_energy", "A011"),
        ("2_", "01_research/A_falsifiers/A015_maxwell_2_dynamical_field", "A015"),
        ("3_", "01_research/A_falsifiers/A012_maxwell_3_physical_lines", "A012"),
        ("4_", "01_research/A_falsifiers/A013_maxwell_4_field_null", "A013"),
        ("5_", "01_research/A_falsifiers/A014_maxwell_5_reciprocal_figures", "A014"),
    ],
    "SST_Kelvin_Floquet": [
        ("Kelvin_Kirchhoff_", "01_research/A_falsifiers/A019_kelvin_kirchhoff_evanescent_core", "A019"),
        ("Kelvin_Joule_", "01_research/A_falsifiers/A032_kelvin_joule_transient_energy", "A032"),
        ("SST_Kelvin_Floquet_Workbench_", "01_research/C_dynamics/C006_kelvin_floquet_workbench", "C006"),
    ],
    "SST_chi_phase_research": [
        ("sst_chi_phase_package_", "01_research/C_dynamics/C001_chi_phase_track_b", "C001"),
        ("sstcore_chiE_local", "01_research/C_dynamics/C003_chie_local_biot_savart", "C003"),
    ],
    "SST_Hopf_Benchmark": [
        ("SST_Hopf_Benchmark_Packet", "01_research/D_benchmarks/D005_hopf_benchmark", "D005"),
        ("SST_Hopf_cpp_pybind", "01_research/D_benchmarks/D005_hopf_benchmark", "D005"),
    ],
    "SST_horn_bem_research": [
        ("sst_horn_dirichlet", "01_research/B_closures/B003_horn_bem", "B003"),
        ("sst_horn_neumann", "01_research/B_closures/B003_horn_bem", "B003"),
    ],
    "SST_ideal_trefoil_biot_research": [
        # CATALOG_v0.1.md, 02_libraries: "No D_numerics in this freeze;
        # sst_trefoil_bs travels with C002." All three children stay together.
        ("sst_ideal_trefoil_biot_package", "01_research/C_dynamics/C002_ideal_trefoil_biot", "C002"),
        ("sst_3d_collider_robust", "01_research/C_dynamics/C002_ideal_trefoil_biot", "C002"),
        ("sst_trefoil_bs", "01_research/C_dynamics/C002_ideal_trefoil_biot", "C002"),
    ],
    "SST_Route_I_relative_entropy_PoC": [
        ("SST_Route_I_relative_entropy_PoC_", "01_research/F_exploratory/F002_route_i_relative_entropy_poc", "F002"),
        ("routeI_heat_guard_patch_bundle", "01_research/F_exploratory/F002_route_i_relative_entropy_poc", "F002"),
    ],
    "Knot_Library": [
        ("SST_Knot_Library", "02_libraries/A_knot_libraries/A002_knot_library", "A002"),
        ("Sources", "03_data/A_knots/06_knot_library/Sources", ""),
        ("Derived", "03_data/A_knots/06_knot_library/Derived", ""),
        ("Registry", "03_data/A_knots/06_knot_library/Registry", ""),
        ("Quarantine", "03_data/A_knots/06_knot_library/Quarantine", ""),
    ],
    # The early chi-phase packages here are the ancestors of Track B, one lineage.
    # sst_taxonomy_starter_* carried the pre-freeze id F007; the catalog now lists it
    # as F004 (F003 is coil_lab).
    "SST_Trefoil_Closure": [
        ("sst_chi_phase_package", "01_research/C_dynamics/C001_chi_phase_track_b", "C001"),
        ("sst_taxonomy_starter", "01_research/F_exploratory/F004_taxonomy_starter", "F004"),
        ("multisector_fit_results", "03_data/D_generated/trefoil_closure", ""),
        ("exports", "03_data/D_generated/trefoil_closure", ""),
        ("phi-3_1", "03_data/D_generated/trefoil_closure", ""),
        ("_dashboard_conflict", "09_archive/trefoil_closure", ""),
        ("archive", "09_archive/trefoil_closure", ""),
        ("build", "DELETE/SST_Trefoil_Closure", ""),
    ],
}

# Container rows to drop outright because a correct child-level row already exists.
DROP_CONTAINER_ROWS: set[tuple[str, str]] = {
    ("experiments", "01_research/04_tools/D_compute/sycl_probes"),
}


def child_dirs(container: str) -> list[str]:
    root = WB / container
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "__")))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    with PM.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    out: list[dict[str, str]] = []
    changed = 0
    for row in rows:
        old = row["old_path"]

        if (old, row["new_path"]) in DROP_CONTAINER_ROWS:
            changed += 1
            continue

        if old in SPLITS and row["phase"].startswith("SP06"):
            continue  # replaced wholesale below

        out.append(row)

    # Re-emit split containers at child granularity.
    for container, rules in SPLITS.items():
        children = child_dirs(container)
        matched: set[str] = set()
        for prefix, new_path, cid in rules:
            hits = [c for c in children if c.startswith(prefix)]
            for child in hits:
                matched.add(child)
                domain, letter = new_path.split("/")[0], new_path.split("/")[1]
                out.append({
                    "old_path": f"{container}/{child}",
                    "new_path": f"{new_path}/{child}",
                    "domain": domain,
                    "letter": letter,
                    "catalog_id": cid,
                    "kind": "code",
                    "phase": "SP06",
                    "junction": "yes",
                    "status": "pending",
                    "note": f"container_split of {container}",
                })
                changed += 1
        leftover = [c for c in children if c not in matched]
        for child in leftover:
            out.append({
                "old_path": f"{container}/{child}",
                "new_path": "",
                "domain": "", "letter": "", "catalog_id": "", "kind": "",
                "phase": "SP06", "junction": "no", "status": "unassigned",
                "note": f"UNASSIGNED child of {container} - needs a destination",
            })
            changed += 1

    news = [r["new_path"] for r in out if r["new_path"]]
    dupes = {p for p in news if news.count(p) > 1}
    unassigned = [r for r in out if r["status"] == "unassigned"]

    print(f"rows before : {len(rows)}")
    print(f"rows after  : {len(out)}")
    print(f"rows changed: {changed}")
    print(f"duplicate new_path after fix: {len(dupes)}")
    for d in sorted(dupes):
        print(f"   {d}")
    print(f"unassigned children: {len(unassigned)}")
    for r in unassigned:
        print(f"   {r['old_path']}")

    if args.apply:
        with PM.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(out)
        print(f"\nWROTE {PM}")
    else:
        print("\n(dry run - pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
