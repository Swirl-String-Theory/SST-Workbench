"""Import Workbench material that only exists in Downloads.

Three categories, each with its own home in the catalog:

* `.stl` / `.3mf` / `.gcode`  -> 03_data/D_generated/D001_3d_exports/
* pack `.zip`                 -> 09_archive/restore/<theme>/
* pack `.patch` / `.diff`     -> 09_archive/restore/Falsifiers/

SST_CANON material is deliberately excluded: the Workbench is not the canonical theory
source, that lives in the SwirlStringTheory repository.

Files are copied, never moved, so Downloads stays intact. Anything already present in
the tree under the same name is skipped.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
DOWNLOADS = Path.home() / "Downloads"

STL_HOME = WB / "03_data" / "D_generated" / "D001_3d_exports"
ARCHIVE = WB / "09_archive" / "restore"

GEOMETRY_SUFFIXES = {".stl", ".3mf", ".gcode"}
PATCH_SUFFIXES = {".patch", ".diff"}

#: Canon material belongs to SwirlStringTheory, not here.
CANON = re.compile(r"(sst[_-]?canon|sstcore|canon_v0|sst-\d+_|sst\d\d_)", re.I)

#: Names that identify Workbench research packs and their patches.
PACK = re.compile(
    r"(falsifier|knot_?geometry|knot_?library|knotplot|katlas|trefoil|maxwell|"
    r"helmholtz|einstein|kelvin|hopf|planck|wien|galileo|swirl_?clock|modal_?clock|"
    r"threaded_?hole|thread_texture|qhp|fourier_vs_ideal|route_?i|route_?b|"
    r"ptsa|ideal_?links|fremlin|ridgerunner|breathing|chirality|varrow|scii|sciii)",
    re.I,
)

#: zip theme buckets that already exist under 09_archive/restore/
THEMES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"knot_?geometry|knot_?library", re.I), "KnotLibrary"),
    (re.compile(r"knotplot|ridgerunner", re.I), "KnotPlot"),
    (re.compile(r"katlas", re.I), "KnotLibrary"),
    (re.compile(r"maxwell", re.I), "Maxwell"),
    (re.compile(r"kelvin|floquet", re.I), "KelvinFloquet"),
    (re.compile(r"trefoil|ptsa", re.I), "Trefoil"),
    (re.compile(r"route_?i", re.I), "Route_I"),
    (re.compile(r"route_?b|bem", re.I), "RouteB_BEM"),
    (re.compile(r"hopf", re.I), "Hopf"),
    (re.compile(r"ideal_?links", re.I), "IdealLinks"),
    (re.compile(r"fremlin|fourier", re.I), "Datasets"),
    (re.compile(r"dashboard", re.I), "Misc"),
]
DEFAULT_THEME = "Falsifiers"


DUP = re.compile(r"\s*\(\d+\)(?=\.[^.]+$)")


def clean_name(name: str) -> str:
    """Strip the browser's `(1)` duplicate marker."""
    return DUP.sub("", name)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def existing_names() -> set[str]:
    skip = {".git", ".venv", "node_modules", "__pycache__", ".tmp.driveupload"}
    out: set[str] = set()
    for path in WB.rglob("*"):
        if set(path.parts) & skip:
            continue
        if path.is_file():
            out.add(clean_name(path.name).lower())
    return out


def theme_for(name: str) -> str:
    for pattern, theme in THEMES:
        if pattern.search(name):
            return theme
    return DEFAULT_THEME


def plan() -> list[tuple[Path, Path, str]]:
    have = existing_names()
    jobs: list[tuple[Path, Path, str]] = []

    for item in sorted(DOWNLOADS.iterdir()):
        if not item.is_file():
            continue
        suffix = item.suffix.lower()
        name = clean_name(item.name)
        if name.lower() in have:
            continue

        if suffix in GEOMETRY_SUFFIXES:
            jobs.append((item, STL_HOME / name, "3d geometry"))
            continue

        if CANON.search(name):
            continue  # belongs to SwirlStringTheory

        if suffix in PATCH_SUFFIXES and PACK.search(name):
            jobs.append((item, ARCHIVE / "Falsifiers" / name, "pack patch"))
            continue

        if suffix == ".zip" and PACK.search(name):
            jobs.append((item, ARCHIVE / theme_for(name) / name, "pack archive"))

    return jobs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    jobs = plan()
    by_kind: dict[str, list[tuple[Path, Path]]] = {}
    for src, dst, kind in jobs:
        by_kind.setdefault(kind, []).append((src, dst))

    total_mb = 0.0
    for kind in sorted(by_kind):
        rows = by_kind[kind]
        size = sum(s.stat().st_size for s, _ in rows) / 1024 / 1024
        total_mb += size
        print(f"\n=== {kind}: {len(rows)} files, {size:.1f} MB ===")
        for src, dst in rows:
            print(f"  {src.stat().st_size / 1024 / 1024:8.1f} MB  {src.name}")
            print(f"           -> {dst.relative_to(WB).as_posix()}")

    print(f"\ntotal: {len(jobs)} files, {total_mb:.1f} MB")

    if not args.apply:
        print("(dry run)")
        return 0

    copied = skipped = 0
    for src, dst, _kind in jobs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and sha256(dst) == sha256(src):
            skipped += 1
            continue
        shutil.copy2(src, dst)
        copied += 1
    print(f"\ncopied {copied}, skipped {skipped} identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
