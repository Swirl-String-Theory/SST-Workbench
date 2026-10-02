"""Stage exactly the files import_from_downloads.py copied in.

`git add -f 09_archive/restore` would force-add all 666 archive zips (3.6 GB), most of
which are deliberately untracked. This recomputes the same destination list and stages
only those paths.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_from_downloads as imp  # noqa: E402

WB = imp.WB


def destinations() -> list[Path]:
    """Rebuild the destination list from the Downloads side, ignoring existence."""
    out: list[Path] = []
    for item in sorted(imp.DOWNLOADS.iterdir()):
        if not item.is_file():
            continue
        suffix = item.suffix.lower()
        name = imp.clean_name(item.name)

        if suffix in imp.GEOMETRY_SUFFIXES:
            out.append(imp.STL_HOME / name)
        elif imp.CANON.search(name):
            continue
        elif suffix in imp.PATCH_SUFFIXES and imp.PACK.search(name):
            out.append(imp.ARCHIVE / "Falsifiers" / name)
        elif suffix == ".zip" and imp.PACK.search(name):
            out.append(imp.ARCHIVE / imp.theme_for(name) / name)
    return [p for p in out if p.is_file()]


def main() -> int:
    paths = destinations()
    rels = sorted({p.relative_to(WB).as_posix() for p in paths})
    print(f"staging {len(rels)} files")
    total = sum((WB / r).stat().st_size for r in rels) / 1024 / 1024
    print(f"total {total:.1f} MB")

    # -f because *.zip is globally ignored; these are pack archives we do want tracked.
    for i in range(0, len(rels), 50):
        chunk = rels[i : i + 50]
        proc = subprocess.run(
            ["git", "-c", "core.longpaths=true", "add", "-f", *chunk],
            cwd=WB, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr.strip())
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
