"""Report Downloads content that looks like Workbench material but is not here yet.

Compares every candidate file in the Downloads folder against three places:

* `09_archive/restore/` - the central zip store
* the extracted family tree - a pack whose directory already exists needs no zip
* the rest of the working tree - by exact filename

A zip is only "missing" if neither the archive nor an extracted directory accounts for
it. Names are matched case-insensitively and with the `(1)`-style browser duplicate
suffix stripped.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Downloads holds filenames with characters cp1252 cannot encode (for example the
# "AEther" ligature), which crashes printing on a default Windows console.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"

#: extensions worth considering as Workbench material
CANDIDATE_SUFFIXES = {
    ".zip", ".stl", ".3mf", ".gcode", ".patch", ".diff", ".tar", ".gz", ".7z",
    ".md", ".csv", ".json", ".txt", ".tex", ".yaml", ".yml",
}

#: Names that look like SST research material. Downloads holds 21 GB of games,
#: drivers and installers; only what matches this is worth reporting.
RELEVANT = re.compile(
    r"(sst|swirl|knot|trefoil|falsifier|maxwell|helmholtz|einstein|kelvin|"
    r"planck|hopf|vortex|fermat|ridgerunner|katlas|fremlin|gilbert|"
    r"chi_?phase|chie|routeb|route_b|route_i|holonomy|floquet|qhp|"
    r"coil|rodin|gear|axle|torus|starship|drone|tpu_frame|baseplate|"
    r"canon|ideal|linkinfo|braid|jones|alexander)",
    re.I,
)

#: Even among matches, these are other repositories or unrelated projects.
NOISE = re.compile(
    r"(sstcore-v|godot|wolvenkit|ketogame|katogame|tinyroom|kato_|mula-b|"
    r"chat-gpt-backup|cursor_presentation|cursor\.tar|node-v|"
    r"drv_audio|sw_ippp|aisuite|nahimic|illusttraties|notebook_2015)",
    re.I,
)

DUP_SUFFIX = re.compile(r"\s*\(\d+\)$")


def norm(name: str) -> str:
    stem = Path(name).stem
    stem = DUP_SUFFIX.sub("", stem)
    return stem.lower()


def workbench_index() -> tuple[dict[str, list[Path]], set[str], set[str]]:
    """(filename -> paths, normalised file stems, normalised directory names)."""
    by_name: dict[str, list[Path]] = defaultdict(list)
    stems: set[str] = set()
    dirs: set[str] = set()
    skip = {".git", ".venv", "node_modules", "__pycache__", ".tmp.driveupload", "DELETE"}
    for path in WB.rglob("*"):
        parts = set(path.parts)
        if parts & skip:
            continue
        try:
            if path.is_dir():
                dirs.add(norm(path.name))
            elif path.is_file():
                by_name[path.name.lower()].append(path)
                stems.add(norm(path.name))
        except OSError:
            continue
    return by_name, stems, dirs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-mb", type=float, default=0.0)
    args = ap.parse_args()

    if not DOWNLOADS.is_dir():
        print(f"no Downloads folder at {DOWNLOADS}")
        return 1

    by_name, stems, dirs = workbench_index()
    print(f"workbench index: {len(by_name)} filenames, {len(dirs)} directories\n")

    present: list[tuple[str, str]] = []
    missing: list[tuple[float, Path, str]] = []

    for item in sorted(DOWNLOADS.iterdir()):
        if not item.is_file() or item.suffix.lower() not in CANDIDATE_SUFFIXES:
            continue
        if not RELEVANT.search(item.name) or NOISE.search(item.name):
            continue
        size_mb = item.stat().st_size / 1024 / 1024
        if size_mb < args.min_mb:
            continue

        key = norm(item.name)
        if item.name.lower() in by_name:
            present.append((item.name, "same filename in tree"))
        elif key in dirs:
            present.append((item.name, "extracted directory exists"))
        elif key in stems:
            present.append((item.name, "same stem in tree"))
        else:
            missing.append((size_mb, item, item.suffix.lower()))

    print(f"=== already covered: {len(present)} ===")
    for name, why in present[:15]:
        print(f"  {name}  ({why})")
    if len(present) > 15:
        print(f"  ... and {len(present) - 15} more")

    print(f"\n=== not found in the workbench: {len(missing)} ===")
    by_ext: dict[str, list[tuple[float, Path]]] = defaultdict(list)
    for size_mb, path, ext in missing:
        by_ext[ext].append((size_mb, path))
    for ext in sorted(by_ext):
        rows = sorted(by_ext[ext], reverse=True)
        total = sum(s for s, _ in rows)
        print(f"\n  {ext}  ({len(rows)} files, {total:.1f} MB)")
        for size_mb, path in rows[:40]:
            print(f"     {size_mb:8.1f} MB  {path.name}")
        if len(rows) > 40:
            print(f"     ... and {len(rows) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
