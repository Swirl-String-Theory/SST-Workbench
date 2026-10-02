"""Repoint path_map destinations after the catalog realignment.

Moving four families to their catalog ids left path_map (and therefore the junction
layer) aimed at directories that no longer exist, which is what bootstrap_junctions
reported.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"

B = "01_research/B_closures"
C = "01_research/C_dynamics"
E = "01_research/E_pipelines"
D = "01_research/D_benchmarks"
T = "04_tools/A_geometry"

#: old new_path prefix -> (new new_path prefix, catalog_id)
REPOINT: dict[str, tuple[str, str]] = {
    f"{B}/B003_planck_routes_a_to_d_equivalence": (f"{B}/B002_planck_routes_a_to_d", "B002"),
    f"{B}/B004_planck_routes_v3_preregistered": (f"{B}/B002_planck_routes_a_to_d", "B002"),
    f"{T}/A003_knotplot_qhp_sweep_generator": (f"{E}/E007_knotplot_qhp_sweep_generator", "E007"),
    f"{C}/C006_uq_twisted_vortex_ring": (f"{C}/C007_uq_twisted_vortex_ring", "C007"),
    f"{B}/B001_derive_constants/schrodinger_gate": (f"{D}/D001_schrodinger_gate_constants_audit", "D001"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    changed = 0

    for row in rows:
        new = row["new_path"]
        for old_prefix, (new_prefix, cid) in REPOINT.items():
            if new == old_prefix or new.startswith(old_prefix + "/"):
                row["new_path"] = new_prefix + new[len(old_prefix):]
                row["catalog_id"] = cid
                note = row["note"] or ""
                if "realigned" not in note:
                    row["note"] = (note + "; " if note else "") + "realigned to the frozen catalog id"
                changed += 1
                print(f"  {old_prefix}\n     -> {row['new_path']}  [{cid}]")
                break

    print(f"\nrows repointed: {changed}")
    if args.apply:
        with PM.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"WROTE {PM}")
    else:
        print("(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
