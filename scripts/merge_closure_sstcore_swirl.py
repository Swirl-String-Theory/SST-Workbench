#!/usr/bin/env python3
"""Merge experiments/trefoil/closure/{sstcore,swirl} into SST_Trefoil_Closure.

swirl is a pure subset of sstcore (verified at plan time). Union = sstcore
content (excluding the trefoil_closure stub). Conflicts with existing
SST_Trefoil_Closure paths go to SST_Trefoil_Closure/_dashboard_conflict/.

Usage:
  python scripts/merge_closure_sstcore_swirl.py --dry-run
  python scripts/merge_closure_sstcore_swirl.py
"""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
CLOSURE = WB / "experiments" / "trefoil" / "closure"
SRC_SST = CLOSURE / "sstcore"
SRC_SWIRL = CLOSURE / "swirl"
DEST = WB / "SST_Trefoil_Closure"
CONFLICT = DEST / "_dashboard_conflict"

SKIP_PREFIXES = ("trefoil_closure/", "__pycache__/")
SKIP_NAMES = {".pyc"}

STUB_CLOSURE = """# trefoil closure sources (relocated)

Dashboard leftovers from `sstcore/` and `swirl/` were merged into:

`SST_Trefoil_Closure/`

(The nested `trefoil_closure/` trees were merged there earlier.)
"""


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            out.append(Path(dirpath) / name)
    return out


def rel_key(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def should_skip(rel: str) -> bool:
    if rel == "trefoil_closure/README.md":
        return True
    return any(rel.startswith(p) for p in SKIP_PREFIXES)


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path)
    except OSError:
        r = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(path)],
            capture_output=True,
            text=True,
        )
        if path.exists():
            raise RuntimeError(f"Failed to remove {path}: {r.stderr}")


def merge(dry_run: bool) -> int:
    if not SRC_SST.is_dir() or not SRC_SWIRL.is_dir():
        print("ERROR: expected sstcore/ and swirl/ under experiments/trefoil/closure", file=sys.stderr)
        return 1
    if not DEST.is_dir():
        print(f"ERROR: missing destination {DEST}", file=sys.stderr)
        return 1

    # Verify swirl subset of sstcore (ignoring stubs/pycache)
    sst_rels = {rel_key(SRC_SST, p) for p in iter_files(SRC_SST) if not should_skip(rel_key(SRC_SST, p))}
    swirl_rels = {
        rel_key(SRC_SWIRL, p) for p in iter_files(SRC_SWIRL) if not should_skip(rel_key(SRC_SWIRL, p))
    }
    only_swirl = sorted(swirl_rels - sst_rels)
    if only_swirl:
        print(f"ERROR: swirl has unique paths; aborting. sample={only_swirl[:10]}", file=sys.stderr)
        return 1
    for rel in sorted(swirl_rels & sst_rels):
        if not filecmp.cmp(SRC_SST / rel, SRC_SWIRL / rel, shallow=False):
            print(f"ERROR: sstcore/swirl content differ for {rel}", file=sys.stderr)
            return 1

    moved = skipped_ident = conflicted = 0
    for src in sorted(iter_files(SRC_SST), key=lambda p: rel_key(SRC_SST, p)):
        rel = rel_key(SRC_SST, src)
        if should_skip(rel):
            continue
        dst = DEST / rel
        if dst.exists():
            if filecmp.cmp(src, dst, shallow=False):
                skipped_ident += 1
                if not dry_run:
                    src.unlink()
                print(f"SKIP identical {rel}")
                continue
            # conflict: keep dest, park dashboard copy
            alt = CONFLICT / rel
            if dry_run:
                print(f"CONFLICT {rel} -> _dashboard_conflict/{rel}")
            else:
                alt.parent.mkdir(parents=True, exist_ok=True)
                if alt.exists():
                    raise FileExistsError(alt)
                shutil.move(str(src), str(alt))
            conflicted += 1
            continue
        if dry_run:
            print(f"MOVE {rel}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        moved += 1

    print(
        f"summary moved={moved} skipped_identical={skipped_ident} "
        f"conflicted={conflicted} swirl_subset_ok=1"
    )

    if dry_run:
        print(f"DRY would remove {SRC_SST} and {SRC_SWIRL}; write closure stub")
        return 0

    force_rmtree(SRC_SST)
    force_rmtree(SRC_SWIRL)
    CLOSURE.mkdir(parents=True, exist_ok=True)
    (CLOSURE / "README.md").write_text(STUB_CLOSURE, encoding="utf-8")
    print(f"STUB {CLOSURE.relative_to(WB)}/README.md")
    print(f"DEST files now ~{sum(1 for _ in DEST.rglob('*') if _.is_file())}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return merge(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
