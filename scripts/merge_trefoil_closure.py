#!/usr/bin/env python3
"""Union-merge nested trefoil_closure trees into Workbench-root SST_Trefoil_Closure.

1. Move swirl/trefoil_closure -> SST_Trefoil_Closure
2. Move sstcore-only relative paths into the destination
3. Remove remaining sstcore/trefoil_closure content
4. Write stub README pointers under the old nested paths

Usage:
  python scripts/merge_trefoil_closure.py --dry-run
  python scripts/merge_trefoil_closure.py
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CLOSURE = WB / "experiments" / "trefoil" / "closure"
SRC_SWIRL = CLOSURE / "swirl" / "trefoil_closure"
SRC_SST = CLOSURE / "sstcore" / "trefoil_closure"
DEST = WB / "SST_Trefoil_Closure"

STUB_TEXT = """# trefoil_closure (relocated)

Merged into the Workbench root:

`SST_Trefoil_Closure/`

(relative from here: `../../../../SST_Trefoil_Closure/`)
"""


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            out.append(Path(dirpath) / name)
    return out


def rel_set(root: Path) -> set[str]:
    return {str(p.relative_to(root)).replace("\\", "/") for p in iter_files(root)}


def count_files(root: Path) -> int:
    return len(iter_files(root))


def only_in_left(left: Path, right: Path) -> list[str]:
    return sorted(rel_set(left) - rel_set(right))


def assert_identical_overlaps(left: Path, right: Path) -> list[str]:
    """Return overlapping relative paths; raise if any differ in content."""
    both = sorted(rel_set(left) & rel_set(right))
    mismatches: list[str] = []
    for rel in both:
        a = left / rel
        b = right / rel
        if not filecmp.cmp(a, b, shallow=False):
            mismatches.append(rel)
    if mismatches:
        raise RuntimeError(
            f"{len(mismatches)} overlapping files differ in content; aborting. "
            f"First: {mismatches[:5]}"
        )
    return both


def write_stub(path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"STUB {path.relative_to(WB)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(STUB_TEXT, encoding="utf-8")
    print(f"STUB {path.relative_to(WB)}")


def clear_tree_keep_nothing(root: Path, dry_run: bool) -> None:
    if not root.exists():
        return
    if dry_run:
        print(f"RMDIR {root.relative_to(WB)} ({count_files(root)} files)")
        return
    try:
        shutil.rmtree(root)
    except OSError as exc:
        print(f"WARN shutil.rmtree failed ({exc}); trying cmd rmdir")
        import subprocess

        r = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(root)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0 or root.exists():
            raise RuntimeError(f"Failed to remove {root}: {r.stderr}") from exc
    print(f"RMDIR {root.relative_to(WB)}")


def merge(dry_run: bool) -> int:
    if not SRC_SWIRL.is_dir():
        print(f"ERROR: missing {SRC_SWIRL}", file=sys.stderr)
        return 1
    if not SRC_SST.is_dir():
        print(f"ERROR: missing {SRC_SST}", file=sys.stderr)
        return 1
    if DEST.exists():
        print(f"ERROR: destination already exists: {DEST}", file=sys.stderr)
        return 1

    both = assert_identical_overlaps(SRC_SST, SRC_SWIRL)
    sst_only = only_in_left(SRC_SST, SRC_SWIRL)
    swirl_only = only_in_left(SRC_SWIRL, SRC_SST)
    print(
        f"overlap identical={len(both)} sstcore_only={len(sst_only)} "
        f"swirl_only={len(swirl_only)}"
    )
    print(f"sstcore files={count_files(SRC_SST)} swirl files={count_files(SRC_SWIRL)}")

    # 1) Move swirl tree to destination
    if dry_run:
        print(f"MOVE {SRC_SWIRL.relative_to(WB)} -> {DEST.relative_to(WB)}")
    else:
        shutil.move(str(SRC_SWIRL), str(DEST))
        print(f"MOVE {SRC_SWIRL.relative_to(WB)} -> {DEST.relative_to(WB)}")

    # 2) Move sstcore-only paths into destination
    for rel in sst_only:
        src = SRC_SST / rel
        dst = DEST / rel
        if dry_run:
            print(f"UNION {src.relative_to(WB)} -> {dst.relative_to(WB)}")
            continue
        if dst.exists():
            raise FileExistsError(f"Unexpected existing dest for sstcore-only: {dst}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"UNION {rel}")

    # 3) Remove remaining sstcore trefoil_closure tree
    clear_tree_keep_nothing(SRC_SST, dry_run)

    # 4) Stubs at old nested paths
    write_stub(SRC_SST / "README.md", dry_run)
    write_stub(SRC_SWIRL / "README.md", dry_run)

    expected = len(both) + len(sst_only) + len(swirl_only)
    if not dry_run:
        got = count_files(DEST)
        print(f"DEST files={got} expected~={expected}")
        if got != expected:
            # __pycache__ exclusion can make swirl walk differ from DEST if any slipped
            print(f"WARN count mismatch (got {got}, expected {expected})")
    else:
        print(f"DRY expected DEST files~={expected}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return merge(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
