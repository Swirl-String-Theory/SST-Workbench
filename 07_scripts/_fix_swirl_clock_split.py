"""Split the Intrinsic Modal Swirl Clock container into its four families.

path_map.csv carried three SP06 rows whose old_path was the *container*
`SST_Intrinsic_Modal_Swirl_Clock` with three different destinations. The first row to
run moved the whole container into A035, so SCII, SCIIb and SCIII ended up inside the
Intrinsic family instead of getting their own.

This rewrites those rows to child granularity, sourced from where the children
actually are now (inside A035), and adds rows for the outputs and patch files that
belong to each family.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"

A035 = "01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock"
OLD_ROOT = "SST_Intrinsic_Modal_Swirl_Clock"

# prefix -> (destination, catalog_id)
FAMILIES = {
    "SST_SCII_Intrinsic_Modal_Phase_Swirl_Clock": (
        "01_research/A_falsifiers/A036_scii_intrinsic_modal_phase_clock", "A036",
    ),
    "SST_SCIIb_Frozen_Modal_Pair_Subspace_Phase_Clock": (
        "01_research/A_falsifiers/A039_sciib_frozen_modal_pair_phase_clock", "A039",
    ),
    "SST_SCIIb_v0.1.0_to_v0.1.1": (
        "01_research/A_falsifiers/A039_sciib_frozen_modal_pair_phase_clock", "A039",
    ),
    "SST_SCIII_Koopman_DMD_Complex_Phase_Clock": (
        "01_research/A_falsifiers/A040_sciii_koopman_dmd_phase_clock", "A040",
    ),
}


def classify(name: str) -> tuple[str, str] | None:
    for prefix, dest in FAMILIES.items():
        if name.startswith(prefix):
            return dest
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())

    # Drop the three container-level rows; they are superseded.
    kept = [
        r
        for r in rows
        if not (r["old_path"] == OLD_ROOT and r["status"] == "pending")
    ]
    dropped = len(rows) - len(kept)

    new_rows: list[dict[str, str]] = []

    # Children already sitting in A035 that belong elsewhere.
    a035 = WB / A035
    if a035.is_dir():
        for entry in sorted(a035.iterdir()):
            dest = classify(entry.name)
            if dest is None:
                continue
            new_path, cid = dest
            new_rows.append({
                "old_path": f"{A035}/{entry.name}",
                "new_path": f"{new_path}/{entry.name}",
                "domain": "01_research", "letter": "A_falsifiers",
                "catalog_id": cid, "kind": "code", "phase": "SP06",
                "junction": "no", "status": "pending",
                "note": "split out of A035; container row moved the whole tree",
            })

    # Anything still stranded at the old root (a locked directory).
    old = WB / OLD_ROOT
    if old.is_dir():
        for entry in sorted(old.iterdir()):
            dest = classify(entry.name)
            if dest is None:
                continue
            new_path, cid = dest
            new_rows.append({
                "old_path": f"{OLD_ROOT}/{entry.name}",
                "new_path": f"{new_path}/{entry.name}",
                "domain": "01_research", "letter": "A_falsifiers",
                "catalog_id": cid, "kind": "code", "phase": "SP06",
                "junction": "no", "status": "pending",
                "note": "stranded at old root after container move",
            })

    out = kept + new_rows
    print(f"container rows dropped : {dropped}")
    print(f"child rows added       : {len(new_rows)}")
    for r in new_rows:
        print(f"  {r['catalog_id']}  {r['old_path']}")

    if args.apply:
        with PM.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(out)
        print(f"\nWROTE {PM}")
    else:
        print("\n(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
