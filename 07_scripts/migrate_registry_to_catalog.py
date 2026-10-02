"""SP08: give every falsifier_registry entry a catalog_id.

The registry resolves packs with `pack_glob`, matched against top-level directory and
zip names. Every one of those globs is stale: the directories moved and the ids are now
the stable identity. This adds `catalog_id` alongside the glob rather than replacing it,
because the glob is still the only way to find a pack inside `09_archive/restore/`,
where zip filenames keep the historical naming forever.

Matching is done against FAMILY.yaml: a glob matches a family when it matches any of its
legacy paths, its version directory names, or its slug.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
REGISTRY = WB / "falsifier_registry.yaml"

#: Globs written before SP06 split their container, so they now match several families.
#: The registry entry is about the family the container was named after. A005 resolves
#: to nothing because the catalog marks it reserved and archive-only.
OVERRIDES = {
    "SST_Trefoil_Lobe_Orientation*": "A021",   # not A023/A031, which SP06 split out
    "SST_Threaded_Hole_Substrate*": "A024",    # not A025, the Local Thread Texture family
    "SST_finite_core_c2*": "A005",             # reserved, no working-tree package
}

ENTRY_ID = re.compile(r"^\s*-\s*id:\s*(\S+)")
PACK_GLOB = re.compile(r"^(\s*)pack_glob:\s*[\"']?([^\"'\n]+)[\"']?\s*$")
CATALOG_ID = re.compile(r"^\s*catalog_id:")


def families() -> list[tuple[str, list[str]]]:
    """(catalog_id, [searchable names]) for every family with a FAMILY.yaml."""
    out: list[tuple[str, list[str]]] = []
    # 05_apps holds families one level shallower than the letter-bearing domains.
    found = list(WB.glob("0*/*/*/FAMILY.yaml")) + list(WB.glob("05_apps/*/FAMILY.yaml"))
    for yml in sorted(set(found)):
        text = yml.read_text(encoding="utf-8")
        cid = ""
        names: list[str] = [yml.parent.name]
        for line in text.splitlines():
            if line.startswith("catalog_id:"):
                cid = line.split(":", 1)[1].strip()
            elif line.startswith("slug:"):
                names.append(line.split(":", 1)[1].strip())
            elif line.strip().startswith(("- \"", "directory: \"")):
                names.append(line.split('"')[1] if '"' in line else "")
        names += [p.name for p in yml.parent.iterdir() if p.is_dir()]
        if cid:
            out.append((cid, [n for n in names if n]))
    return out


def match_glob(glob: str, index: list[tuple[str, list[str]]]) -> list[str]:
    hits = []
    for cid, names in index:
        if any(fnmatch.fnmatch(n.lower(), glob.lower()) for n in names):
            hits.append(cid)
    return sorted(set(hits))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    index = families()
    print(f"families with FAMILY.yaml: {len(index)}")

    lines = REGISTRY.read_text(encoding="utf-8").splitlines(keepends=True)
    already = sum(1 for line in lines if CATALOG_ID.match(line))
    out: list[str] = []
    resolved = ambiguous = unmatched = 0

    for line in lines:
        out.append(line)
        m = PACK_GLOB.match(line.rstrip("\n"))
        if not m or already:
            continue
        indent, glob = m.group(1), m.group(2).strip()
        if glob in OVERRIDES:
            out.append(f"{indent}catalog_id: {OVERRIDES[glob]}\n")
            resolved += 1
            print(f"  override   {glob}  -> {OVERRIDES[glob]}")
            continue
        hits = match_glob(glob, index)
        if len(hits) == 1:
            out.append(f"{indent}catalog_id: {hits[0]}\n")
            resolved += 1
        elif hits:
            out.append(f"{indent}catalog_id: {hits[0]}  # ambiguous: {', '.join(hits)}\n")
            ambiguous += 1
            print(f"  AMBIGUOUS  {glob}  -> {', '.join(hits)}")
        else:
            out.append(f"{indent}catalog_id:  # unresolved glob: {glob}\n")
            unmatched += 1
            print(f"  UNRESOLVED {glob}")

    if already:
        print(f"registry already carries {already} catalog_id fields; nothing to do")
        return 0

    print(f"resolved to one family : {resolved}")
    print(f"ambiguous (first used) : {ambiguous}")
    print(f"unresolved             : {unmatched}")

    if args.apply:
        REGISTRY.write_text("".join(out), encoding="utf-8")
        print(f"\nWROTE {REGISTRY.name}")
    else:
        print("\n(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
