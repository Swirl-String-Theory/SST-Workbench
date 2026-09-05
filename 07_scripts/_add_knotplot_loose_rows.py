"""Add SP07 rows for the loose files at the KnotPlot root.

The existing rows cover KnotPlot/*.py and KnotPlot/*_outputs.zip, which leaves 17 files
at the root with no destination: the .kps scene scripts, the .lnk to the external
KnotPlot executable, the run_build wrappers, the READMEs, KnotPlot.zip, and four
reference/output artefacts.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"

TOOL = "04_tools/A_geometry/A001_knotplot"
ARCHIVE = "09_archive/restore/KnotPlot"
REFERENCE = "03_data/D_generated/knotplot_reference"

# (glob, destination, kind, note)
ROWS = [
    ("KnotPlot/*.kps", TOOL, "tooling", "KnotPlot scene scripts"),
    ("KnotPlot/*.lnk", TOOL, "tooling", "shortcut to the external KnotPlot executable"),
    ("KnotPlot/*.js", TOOL, "tooling", "generated knot data consumed by the vortexlab app"),
    ("KnotPlot/*.md", TOOL, "tooling", "tool documentation"),
    ("KnotPlot/run_build*.cmd", TOOL, "tooling", "build wrappers"),
    ("KnotPlot/KnotPlot.zip", ARCHIVE, "archive", "tool distribution archive"),
    ("KnotPlot/trefoil_relaxed_*", REFERENCE, "output", "relaxed trefoil reference artefacts"),
    ("KnotPlot/ideal_3_1_from_kp_radius.txt", REFERENCE, "data", "ideal 3_1 radius reference"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    fields = list(rows[0].keys())
    existing = {r["old_path"] for r in rows}

    new: list[dict[str, str]] = []
    for glob, dest, kind, note in ROWS:
        if glob in existing:
            continue
        matches = sorted(WB.glob(glob))
        if not matches:
            print(f"  (no match) {glob}")
            continue
        parts = dest.split("/")
        new.append({
            "old_path": glob,
            "new_path": dest,
            "domain": parts[0],
            "letter": parts[1] if len(parts) > 1 and parts[1][1:2] == "_" else "",
            "catalog_id": "A001" if dest == TOOL else "",
            "kind": kind,
            "phase": "SP07",
            "junction": "no",
            "status": "pending",
            "note": note,
        })
        print(f"  +{len(matches):3d} files  {glob} -> {dest}")

    print(f"\nnew rows: {len(new)}")
    if args.apply:
        with PM.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows + new)
        print(f"WROTE {PM}")
    else:
        print("(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
