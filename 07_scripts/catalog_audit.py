"""Compare CATALOG_v0.1.md against the directories that actually exist.

Every family in the catalog should have exactly one directory named
`<catalog_id>_<slug>` under its domain-letter, and every such directory should be in
the catalog. Reports both directions plus the version count per family, which SP08
needs to write FAMILY.yaml and SP09 needs to rename version directories.
"""
from __future__ import annotations

import re
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CATALOG = WB / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"

#: domain -> letter directories that hold catalog families
FAMILY_HOMES = {
    "01_research": ["A_falsifiers", "B_closures", "C_dynamics",
                    "D_benchmarks", "E_pipelines", "F_exploratory"],
    "02_libraries": ["A_knot_libraries", "B_finite_core", "D_numerics"],
    "04_tools": ["A_geometry", "B_crawlers", "C_fabrication", "D_compute", "D_proof"],
    "05_apps": [""],
}

ROW = re.compile(r"^\|\s*\*{0,2}([A-F]\d{3})\*{0,2}\s*\|\s*`?([^`|]*)`?\s*\|")
SECTION = re.compile(r"^#+\s*(0\d_[a-z_]+)")


def catalog_entries() -> dict[str, set[str]]:
    """domain -> set of catalog ids listed under it."""
    out: dict[str, set[str]] = {}
    domain = None
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        m = SECTION.match(line)
        if m:
            domain = m.group(1)
            out.setdefault(domain, set())
            continue
        if domain is None:
            continue
        m = ROW.match(line)
        if m:
            out[domain].add(m.group(1))
    return out


def disk_families() -> dict[str, dict[str, Path]]:
    """domain -> {catalog_id: directory}."""
    out: dict[str, dict[str, Path]] = {}
    for domain, letters in FAMILY_HOMES.items():
        found: dict[str, Path] = {}
        for letter in letters:
            base = WB / domain / letter if letter else WB / domain
            if not base.is_dir():
                continue
            for d in base.iterdir():
                if not d.is_dir():
                    continue
                m = re.match(r"^([A-F]\d{3})_", d.name)
                if m:
                    found[m.group(1)] = d
        out[domain] = found
    return out


def version_dirs(family: Path) -> list[Path]:
    """Version directories inside a family, excluding metadata folders."""
    skip = {"_variants", "keys", "references", "__pycache__", ".venv", ".pytest_cache"}
    return sorted(
        d for d in family.iterdir()
        if d.is_dir() and d.name not in skip and not d.name.startswith(".")
    )


def main() -> None:
    cat = catalog_entries()
    disk = disk_families()

    print("=== families on disk, per domain ===")
    total = 0
    for domain in sorted(disk):
        n = len(disk[domain])
        total += n
        print(f"  {domain:<14} {n}")
    print(f"  {'TOTAL':<14} {total}")

    print("\n=== in catalog but no directory ===")
    missing = 0
    for domain, ids in sorted(cat.items()):
        if domain not in disk:
            continue
        gap = sorted(ids - set(disk[domain]))
        for cid in gap:
            print(f"  {domain}  {cid}")
            missing += 1
    print(f"  count: {missing}")

    print("\n=== directory but not in catalog ===")
    extra = 0
    for domain, found in sorted(disk.items()):
        ids = cat.get(domain, set())
        for cid in sorted(set(found) - ids):
            print(f"  {domain}  {cid}  ({found[cid].name})")
            extra += 1
    print(f"  count: {extra}")

    print("\n=== families with no version directory ===")
    flat = 0
    for domain, found in sorted(disk.items()):
        for cid, d in sorted(found.items()):
            if not version_dirs(d):
                print(f"  {domain}  {cid}  {d.name}")
                flat += 1
    print(f"  count: {flat}")

    versions = sum(
        len(version_dirs(d))
        for found in disk.values()
        for d in found.values()
    )
    print(f"\ntotal version directories under families: {versions}")


if __name__ == "__main__":
    main()
