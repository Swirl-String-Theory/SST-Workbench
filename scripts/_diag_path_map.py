"""Ad-hoc diagnostic for path_map.csv integrity (SP04 precondition)."""
from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
PM = WB / "10_docs" / "migration" / "path_map.csv"
CATALOG = WB / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"

DOMAIN = re.compile(r"^(0[1-9]|10)_[a-z_]+$")


def main() -> None:
    rows = list(csv.DictReader(PM.open(encoding="utf-8-sig")))
    print(f"total rows: {len(rows)}")

    print("\n=== DUPLICATE new_path ===")
    counts = collections.Counter(r["new_path"] for r in rows)
    dupes = [(p, n) for p, n in counts.most_common() if n > 1]
    if not dupes:
        print("  none")
    for path, n in dupes:
        print(f"  x{n}  {path}")
        for r in rows:
            if r["new_path"] == path:
                print(f"        <- {r['old_path']}   [{r['phase']}/{r['status']}]")

    print("\n=== MALFORMED new_path (domain nested inside another domain) ===")
    bad = [r for r in rows if any(DOMAIN.match(p) for p in r["new_path"].split("/")[1:])]
    if not bad:
        print("  none")
    for r in bad:
        print(f"  {r['new_path']}   <- {r['old_path']}   [{r['phase']}]")

    print("\n=== new_path with no known domain prefix ===")
    for r in rows:
        head = r["new_path"].split("/")[0]
        if not DOMAIN.match(head) and head != "DELETE":
            print(f"  {r['new_path']}   <- {r['old_path']}")

    print("\n=== catalog_id values not present in CATALOG_v0.1.md ===")
    text = CATALOG.read_text(encoding="utf-8")
    known = set(re.findall(r"\|\s*\*{0,2}([A-F]\d{3})\*{0,2}\s*\|", text))
    seen = []
    for r in rows:
        cid = r["catalog_id"].strip()
        if cid and cid not in known:
            seen.append((r["old_path"], cid, r["new_path"]))
    if not seen:
        print("  none")
    for old, cid, new in seen:
        print(f"  {cid}  <- {old}   -> {new}")

    print("\n=== rows whose old_path is missing on disk ===")
    missing = [r for r in rows if not (WB / r["old_path"]).exists() and "*" not in r["old_path"]]
    print(f"  {len(missing)} rows")
    for r in missing:
        print(f"  [{r['status']:8}] {r['old_path']}")


if __name__ == "__main__":
    main()
