"""Rules for Workbench output archives next to falsifier packs.

Outputs and zip files go to GitHub only as files under 50 MiB:
- sibling ``{pack}_outputs.zip`` if size < 50 MiB (``git add -f``)
- any other pack-adjacent ``.zip`` under 50 MiB (``git add -f``)
- if 50 MiB <= size < 500 MiB, split into 50 MiB ``*.zip.partNN`` (tracked)
- if size >= 500 MiB, keep the zip local only (gitignored)
- unpacked ``outputs/`` stay on disk (gitignored) so git status stays small

Naming matches Trefoil pack_outputs.py, but the stem is ``legacy_dir`` from
``project.json`` once SP09 shortens version directories::

    pack.parent / f"{artifact_stem(pack)}_outputs.zip"
    pack.parent / f"{artifact_stem(pack)}_outputs.zip.part01"
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

_SCRIPTS = str(Path(__file__).resolve().parent)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from output_naming import artifact_stem  # noqa: E402

MIB = 1024 * 1024
PART_BYTES = 50 * MIB
SPLIT_MIN_BYTES = 50 * MIB
SPLIT_MAX_BYTES = 500 * MIB

OUTPUT_DIR_NAMES = ("outputs", "out", "campaigns", "analysis", "logs", "artifacts")
SKIP_ZIP_PARTS = {".venv", "__pycache__", ".git", "node_modules"}
SKIP_COMMIT_DIR_NAMES = SKIP_ZIP_PARTS | {"Restore_Archives"}

_PART_RE = re.compile(r"^(.+_outputs\.zip)\.part(\d+)$", re.I)
_OUTPUTS_ZIP_RE = re.compile(r"_outputs\.zip$", re.I)


def output_zip_path(pack_dir: Path) -> Path:
    """Sibling archive path: ``{parent}/{artifact_stem}_outputs.zip``."""
    pack_dir = Path(pack_dir)
    return pack_dir.parent / f"{artifact_stem(pack_dir)}_outputs.zip"


def part_path(zip_path: Path, index: int) -> Path:
    """1-based part file next to the full zip."""
    if index < 1:
        raise ValueError("part index is 1-based")
    return Path(zip_path).with_name(f"{Path(zip_path).name}.part{index:02d}")


def is_outputs_zip_name(name: str) -> bool:
    return bool(_OUTPUTS_ZIP_RE.search(name)) and not name.lower().endswith(".part")


def parse_part_name(name: str) -> tuple[str, int] | None:
    m = _PART_RE.match(name)
    if not m:
        return None
    return m.group(1), int(m.group(2))


def is_under_50mib(path: Path) -> bool:
    return Path(path).stat().st_size < SPLIT_MIN_BYTES


def output_zip_class(size: int) -> str:
    """Return 'single', 'parts', or 'local_only' for a byte size."""
    if size < SPLIT_MIN_BYTES:
        return "single"
    if size < SPLIT_MAX_BYTES:
        return "parts"
    return "local_only"


def is_commitable_output_artifact(path: Path, *, restore_name: str = "Restore_Archives") -> bool:
    """True if this file should be force-added: zip/part under the 50 MiB rule."""
    p = Path(path)
    if not p.is_file():
        return False
    if restore_name in p.parts or any(part in SKIP_COMMIT_DIR_NAMES for part in p.parts):
        return False
    parsed = parse_part_name(p.name)
    if parsed is not None:
        return True
    name = p.name.lower()
    if name.endswith("_outputs.zip.parts.json") or name.endswith(".zip.sha256"):
        return True
    if p.suffix.lower() != ".zip":
        return False
    return p.stat().st_size < SPLIT_MIN_BYTES


def _output_tree_bytes(pack_dir: Path) -> int:
    pack_dir = Path(pack_dir)
    total = 0
    for name in OUTPUT_DIR_NAMES:
        root = pack_dir / name
        if root.is_file():
            total += root.stat().st_size
        elif root.is_dir():
            for f in root.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
    return total


def iter_commitable_zips(workbench: Path) -> list[Path]:
    """Pack-adjacent ``.zip`` files that pass ``is_commitable_output_artifact``."""
    workbench = Path(workbench)
    found: list[Path] = []
    for z in workbench.rglob("*.zip"):
        if not z.is_file():
            continue
        if any(part in SKIP_COMMIT_DIR_NAMES for part in z.parts):
            continue
        if is_commitable_output_artifact(z):
            found.append(z)
    return found


def ensure_sibling_output_zips(workbench: Path) -> list[Path]:
    """Create missing sibling ``*_outputs.zip`` from unpacked output dirs.

    Skip trees whose unpacked size is already >= 500 MiB; those stay local
    or must be split with the existing ``*_outputs.zip.partNN`` workflow.
    """
    workbench = Path(workbench).resolve()
    created: list[Path] = []
    seen_packs: set[Path] = set()
    for name in ("outputs", "artifacts"):
        for root in workbench.rglob(name):
            if not root.is_dir():
                continue
            if any(part in SKIP_COMMIT_DIR_NAMES for part in root.parts):
                continue
            pack = root.parent
            if pack == workbench or pack in seen_packs:
                continue
            seen_packs.add(pack)
            sibling = output_zip_path(pack)
            if sibling.is_file():
                continue
            if _output_tree_bytes(pack) >= SPLIT_MAX_BYTES:
                continue
            packed = pack_output_dirs(pack)
            if packed is not None:
                created.append(packed)
    return created


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def split_zip_into_parts(zip_path: Path, part_bytes: int = PART_BYTES) -> list[Path]:
    """Write ``name.zip.part01`` … next to *zip_path*. Does not delete the full zip."""
    zip_path = Path(zip_path)
    size = zip_path.stat().st_size
    if size < SPLIT_MIN_BYTES:
        return []
    if size >= SPLIT_MAX_BYTES:
        return []
    parts: list[Path] = []
    index = 1
    with zip_path.open("rb") as src:
        while True:
            chunk = src.read(part_bytes)
            if not chunk:
                break
            dest = part_path(zip_path, index)
            dest.write_bytes(chunk)
            parts.append(dest)
            index += 1
    manifest = Path(str(zip_path) + ".parts.json")
    manifest.write_text(
        json.dumps(
            {
                "zip": zip_path.name,
                "sha256": sha256_file(zip_path),
                "size": size,
                "part_bytes": part_bytes,
                "parts": [p.name for p in parts],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return parts


def join_zip_parts(zip_path: Path) -> Path:
    """Concatenate ``zip.partNN`` into *zip_path* (overwrite)."""
    zip_path = Path(zip_path)
    parts = sorted(
        zip_path.parent.glob(zip_path.name + ".part*"),
        key=lambda p: parse_part_name(p.name)[1] if parse_part_name(p.name) else 0,
    )
    numbered = [p for p in parts if parse_part_name(p.name)]
    if not numbered:
        raise FileNotFoundError(f"no parts for {zip_path.name}")
    with zip_path.open("wb") as out:
        for part in numbered:
            out.write(part.read_bytes())
    return zip_path


def pack_output_dirs(pack_dir: Path) -> Path | None:
    """Zip output-like subdirs of *pack_dir* to the Trefoil sibling zip. None if empty."""
    pack_dir = Path(pack_dir)
    dest = output_zip_path(pack_dir)
    members: list[Path] = []
    for name in OUTPUT_DIR_NAMES:
        root = pack_dir / name
        if root.is_file():
            members.append(root)
        elif root.is_dir():
            for f in root.rglob("*"):
                if not f.is_file():
                    continue
                if any(part in SKIP_ZIP_PARTS for part in f.relative_to(pack_dir).parts):
                    continue
                members.append(f)
    if not members:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in members:
            zf.write(f, arcname=f.relative_to(pack_dir).as_posix())
    sidecar = Path(str(dest) + ".sha256")
    sidecar.write_text(f"{sha256_file(dest)}  {dest.name}\n", encoding="ascii")
    return dest


def prepare_output_archive_for_git(zip_path: Path) -> list[Path]:
    """Return paths that should be ``git add -f``'d for this output zip."""
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        return []
    kind = output_zip_class(zip_path.stat().st_size)
    if kind == "single":
        return [zip_path]
    if kind == "parts":
        parts = split_zip_into_parts(zip_path)
        extra = Path(str(zip_path) + ".parts.json")
        return parts + ([extra] if extra.is_file() else [])
    return []
