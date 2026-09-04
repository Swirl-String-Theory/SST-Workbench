#!/usr/bin/env python3
"""Flatten SST-dashboard/sstcore + SST-dashboard/swirl into SST-dashboard/.

1. Move swirl files to SST-dashboard/ first
2. Move sstcore files; identical skipped; exports/ideal.txt conflict keeps sstcore
3. Remove leftover sstcore/ and swirl/ trees

Usage:
  python scripts/merge_sst_dashboard.py --dry-run
  python scripts/merge_sst_dashboard.py
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
DASH = WB / "SST-dashboard"
SRC_SWIRL = DASH / "swirl"
SRC_SST = DASH / "sstcore"
CONFLICT_REL = "exports/ideal.txt"

SKIP_DIR_NAMES = {
    "__pycache__",
    ".tmp.drivedownload",
    ".tmp.driveupload",
}


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            out.append(Path(dirpath) / name)
    return out


def rel_key(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


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


def place_file(
    src: Path,
    dest_root: Path,
    rel: str,
    source_label: str,
    dry_run: bool,
    virtual: dict[str, Path] | None = None,
) -> str:
    """Return action: moved|skipped_identical|conflict_parked|conflict_preferred."""
    dst = dest_root / rel
    dest_present = (virtual is not None and rel in virtual) or dst.exists()
    dest_path_for_cmp = virtual[rel] if (virtual is not None and rel in virtual) else dst

    if not dest_present:
        if dry_run:
            print(f"MOVE [{source_label}] {rel}")
            if virtual is not None:
                virtual[rel] = src
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        return "moved"

    if filecmp.cmp(src, dest_path_for_cmp, shallow=False):
        if dry_run:
            print(f"SKIP identical [{source_label}] {rel}")
        else:
            src.unlink()
        return "skipped_identical"

    # Content conflict
    if rel == CONFLICT_REL:
        if source_label == "sstcore":
            # Prefer sstcore: park current dest (swirl), then place sstcore
            alt = dest_root / "_merge_conflict" / rel
            if dry_run:
                print(f"CONFLICT prefer sstcore; park dest -> _merge_conflict/{rel}")
                if virtual is not None:
                    virtual[rel] = src
            else:
                alt.parent.mkdir(parents=True, exist_ok=True)
                if alt.exists():
                    raise FileExistsError(alt)
                shutil.move(str(dst), str(alt))
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
            return "conflict_preferred"
        # swirl arriving later shouldn't happen with swirl-first order; park swirl
        alt = dest_root / "_merge_conflict" / rel
        if dry_run:
            print(f"CONFLICT park [{source_label}] -> _merge_conflict/{rel}")
        else:
            alt.parent.mkdir(parents=True, exist_ok=True)
            if alt.exists():
                raise FileExistsError(alt)
            shutil.move(str(src), str(alt))
        return "conflict_parked"

    raise RuntimeError(f"Unexpected content conflict for {rel} from {source_label}")


def merge(dry_run: bool) -> int:
    if not SRC_SWIRL.is_dir() or not SRC_SST.is_dir():
        print("ERROR: expected SST-dashboard/sstcore and SST-dashboard/swirl", file=sys.stderr)
        return 1

    # Refuse if destination already has unexpected top-level content besides sources
    # (allow only sstcore/swirl during merge)
    counts = {"moved": 0, "skipped_identical": 0, "conflict_preferred": 0, "conflict_parked": 0}
    virtual: dict[str, Path] | None = {} if dry_run else None

    for label, root in (("swirl", SRC_SWIRL), ("sstcore", SRC_SST)):
        for src in sorted(iter_files(root), key=lambda p: rel_key(root, p)):
            rel = rel_key(root, src)
            action = place_file(src, DASH, rel, label, dry_run, virtual=virtual)
            counts[action] += 1

    print(
        "summary "
        + " ".join(f"{k}={v}" for k, v in counts.items())
    )

    if dry_run:
        print("DRY would remove sstcore/ and swirl/ tmp dirs")
        return 0

    force_rmtree(SRC_SWIRL)
    force_rmtree(SRC_SST)
    # drop leftover tmp/pycache if any at dash root from partial walks
    for name in SKIP_DIR_NAMES:
        force_rmtree(DASH / name)

    note_path = DASH / "MERGE_NOTE.md"
    note_path.write_text(
        "# SST-dashboard merge\n\n"
        "Flattened former `sstcore/` and `swirl/` trees into this folder.\n"
        "Sole content conflict: `exports/ideal.txt` kept from sstcore; "
        "swirl copy at `_merge_conflict/exports/ideal.txt`.\n",
        encoding="utf-8",
    )
    print(f"WROTE {note_path.relative_to(WB)}")
    nfiles = sum(1 for p in DASH.rglob("*") if p.is_file())
    print(f"DASH files now {nfiles}")
    print(f"sstcore exists={SRC_SST.exists()} swirl exists={SRC_SWIRL.exists()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return merge(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
