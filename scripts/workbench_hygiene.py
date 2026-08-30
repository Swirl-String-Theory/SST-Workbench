"""Copy older/patch zips beside packs; relocate trees to DELETE (no unlink)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

MIB = 1024 * 1024
COPY_LIMIT = 50 * MIB

DOWNLOADS_DIR = Path.home() / "Downloads"
DELETE_ROOT = Path(r"C:\workspace\projects\DELETE")

# (family_dir relative to workbench, filename regex for Downloads/Restore)
FAMILY_ZIP_COPY: list[tuple[str, re.Pattern[str]]] = [
    ("SST_Intrinsic_Modal_Swirl_Clock", re.compile(r"SST_Intrinsic_Modal_Swirl_Clock|SST_SCII", re.I)),
    ("SST_Katlas_Link_Geometry_Conditioning_v2.0.0", re.compile(r"SST_Katlas_Link_Geometry", re.I)),
    ("SST_QHP_Stability_Landscape", re.compile(r"SST_QHP_Stability|SST_KnotPlot_QHP_Sweep_Generator", re.I)),
    ("SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier", re.compile(r"SST_Trefoil_Dynamic_Seed", re.I)),
    ("SST_Chirality_Helicity_Transport_Polarity", re.compile(r"SST_Chirality_Helicity", re.I)),
    ("SST_Breathing_Stretching_Return_Phase_Causality", re.compile(r"SST_Breathing_Stretching", re.I)),
    ("KnotPlot", re.compile(r"Trefoil_Balance_Point_Campaign|KnotPlot_MultiTopology_QHP_Sweep", re.I)),
]

_OUTPUT_ZIP_RE = re.compile(r"(?:^|[_-])outputs?(?:[_-]|\.zip$)|(?:^|[_-])output\.zip$", re.I)
_CHROME_DUP = re.compile(r"\s+\(\d+\)\.zip$", re.I)


def canonical_zip_basename(name: str) -> str:
    return _CHROME_DUP.sub(".zip", name)


def is_output_archive(name: str) -> bool:
    return bool(_OUTPUT_ZIP_RE.search(name))


def is_under_50mib(path: Path) -> bool:
    return path.stat().st_size < COPY_LIMIT


def copy_if_missing(src: Path, dest: Path) -> str:
    """Copy src -> dest unless dest exists with same size. Never deletes src."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if dest.stat().st_size == src.stat().st_size:
            return "skip_exists"
        dest = dest.with_name(dest.stem + "__from_downloads" + dest.suffix)
    shutil.copy2(src, dest)
    return "copy"


def relocate_to_delete(src: Path, workbench: Path, delete_root: Path) -> Path:
    """Move src to delete_root / relative path. No unlink/rmtree of contents."""
    src = Path(src).resolve()
    workbench = Path(workbench).resolve()
    rel = src.relative_to(workbench)
    dest = Path(delete_root) / rel
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return dest


def plan_family_zip_copies(
    workbench: Path,
    downloads: Path,
    *,
    include_outputs: bool = False,
) -> list[tuple[Path, Path]]:
    """List (src, dest) copies of source/hotfix zips < 50 MiB beside family folders."""
    planned: list[tuple[Path, Path]] = []
    if not downloads.is_dir():
        return planned
    for family_rel, pat in FAMILY_ZIP_COPY:
        dest_dir = workbench / family_rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src in sorted(downloads.glob("*.zip")):
            if not src.is_file():
                continue
            if not pat.search(src.name):
                continue
            if not include_outputs and is_output_archive(src.name):
                continue
            if not is_under_50mib(src):
                continue
            dest = dest_dir / canonical_zip_basename(src.name)
            planned.append((src, dest))
    return planned


SWIRL_RELOCATE = [
    "SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.5",
    "SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.6",
    "SST_Intrinsic_Modal_Swirl_Clock/SST_Intrinsic_Modal_Swirl_Clock_Blind_Falsifier_v0.2.2.7",
]

_DIR_UNTRACK = {"outputs", "campaigns", "logs"}
_KNOTPLOT_QHP = {"qhp", "qhp_extended", "qhp_6p3"}


def _posix(rel: str) -> str:
    return rel.replace("\\", "/")


def should_untrack_rel(rel: str, workbench: Path, policy) -> bool:
    """True if a tracked path should leave the git index (file stays on disk)."""
    posix = _posix(rel)
    parts = posix.split("/")
    name = parts[-1]
    path = workbench / posix
    if path.is_file() and policy.is_commitable_output_artifact(path):
        return False
    if "Restore_Archives" in parts and name.lower().endswith(".zip"):
        return True
    if name.lower().endswith(".npz"):
        return True
    if name.lower().endswith(".zip"):
        return True
    if any(part in _DIR_UNTRACK for part in parts):
        return True
    if "Katlas_Sources_v0.2.2_Outputs" in parts:
        return True
    if "KnotPlot" in parts and "out" in parts:
        return True
    if "KnotPlot" in parts and any(part in _KNOTPLOT_QHP for part in parts):
        return True
    return False


def source_zip_present(workbench: Path, folder_rel: str) -> bool:
    name = Path(folder_rel).name + ".zip"
    family = Path(folder_rel).parent
    beside = workbench / family / name
    if beside.is_file():
        return True
    restore = workbench / "Restore_Archives"
    if restore.is_dir():
        return any(p.name == name for p in restore.rglob(name))
    return False
