"""Find container rows whose split collapsed into a single destination.

A container that should split into N families was recorded as N rows all sharing the
*container* as old_path. The first row to run moved the whole tree into its own
destination and the other N-1 were skipped as "missing on disk", so those families
never got created and their content sits inside the first one.

Hit this twice: SST_Intrinsic_Modal_Swirl_Clock (4 families) and
SST_v0_8_19_routes_research (5 families).
"""
from __future__ import annotations

import collections
import csv
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"


def main() -> None:
    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    by_old: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for r in rows:
        by_old[r["old_path"]].append(r)

    affected = 0
    for old, group in sorted(by_old.items()):
        if len(group) < 2:
            continue
        statuses = {r["status"] for r in group}
        if "moved" not in statuses or "skipped" not in statuses:
            continue
        affected += 1
        winner = next(r for r in group if r["status"] == "moved")
        print(f"\n{old}  ({len(group)} rows)")
        print(f"    WON  -> {winner['new_path']}")
        for r in group:
            if r["status"] != "moved":
                print(f"    lost -> {r['new_path']}  [{r['catalog_id']}]")

    print(f"\naffected containers: {affected}")

    print("\n=== catalog families with no directory on disk ===")
    missing = []
    for r in rows:
        cid = r["catalog_id"].strip()
        if not cid or r["status"] != "skipped":
            continue
        new = r["new_path"].strip()
        if new and not (WB / new).exists():
            missing.append((cid, new))
    for cid, new in sorted(set(missing)):
        print(f"  {cid}  {new}")
    print(f"missing family dirs: {len(set(missing))}")


if __name__ == "__main__":
    main()
