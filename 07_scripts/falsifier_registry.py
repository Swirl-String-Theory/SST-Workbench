"""Master falsifier registry: load, validate, resolve pack paths, discover gaps."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

WB = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = WB / "falsifier_registry.yaml"
RESTORE = WB / "Restore_Archives"

PHYSICS_STATUSES = frozenset(
    {"PASS", "FAIL", "INDETERMINATE", "UNTESTED", "REFERENCE_ONLY"}
)
NUMERICS_STATUSES = frozenset({"PASS", "FAIL", "NOT_RUN", "N/A"})
FAMILIES = frozenset({"I", "II", "III", "IV", "V"})

SKIP_DIR_NAMES = frozenset(
    {".git", ".venv", "node_modules", "__pycache__", ".tmp.driveupload", "site-packages"}
)

VER_RE = re.compile(r"v(\d+(?:[._]\d+)*)", re.I)
PACK_MARKER_NAMES = frozenset({"README.md", "run_all.cmd", "pyproject.toml"})


@dataclass
class PackIndex:
    dirs: list[tuple[str, tuple[int, ...], Path]] = field(default_factory=list)
    zips: list[tuple[str, tuple[int, ...], Path]] = field(default_factory=list)


_PACK_INDEX: PackIndex | None = None


def build_pack_index(*, wb: Path = WB, restore: Path = RESTORE) -> PackIndex:
    dirs: list[tuple[str, tuple[int, ...], Path]] = []
    for p in _iter_candidate_dirs(wb):
        if p.parts and p.parts[0] == "Restore_Archives":
            continue
        aliases = [p.name]
        pj = p / "project.json"
        if pj.is_file():
            try:
                legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            except (OSError, json.JSONDecodeError):
                legacy = ""
            if legacy and legacy != p.name:
                aliases.append(legacy)
        for alias in aliases:
            ver = parse_version(alias) or parse_version(p.name)
            if ver is None:
                lower = alias.lower()
                if "stecklov" in lower:
                    ver = (5, 1)
                else:
                    continue
            dirs.append((alias, ver, p))
    zips: list[tuple[str, tuple[int, ...], Path]] = []
    for z in _iter_candidate_zips(restore):
        ver = parse_version(z.name)
        if ver is not None:
            zips.append((z.name, ver, z))
    return PackIndex(dirs=dirs, zips=zips)


def get_pack_index(*, wb: Path = WB, restore: Path = RESTORE) -> PackIndex:
    global _PACK_INDEX
    if _PACK_INDEX is None:
        _PACK_INDEX = build_pack_index(wb=wb, restore=restore)
    return _PACK_INDEX


def reset_pack_index() -> None:
    global _PACK_INDEX
    _PACK_INDEX = None


@dataclass
class ResolvedPack:
    version: tuple[int, ...]
    version_str: str
    working_tree: str | None = None
    archive_zip: str | None = None

    def rel_working(self) -> str:
        return self.working_tree or "—"

    def rel_archive(self) -> str:
        return self.archive_zip or "—"


@dataclass
class RegistryEntry:
    id: str
    family: str
    name: str
    pack_glob: str
    hypothesis: str = ""
    blind: bool = False
    h0: str = ""
    h1: str = ""
    dataset: str = ""
    gate: str = ""
    physics_status: str = "UNTESTED"
    numerics_status: str = "NOT_RUN"
    result_sha256: str | None = None
    next_test: str = ""
    hypothesis_table: int | None = None
    stars: str = ""
    physics_emoji: str = ""
    question: str = ""
    pack_path_hint: str | None = None
    resolved: ResolvedPack | None = field(default=None, repr=False)


def parse_version(text: str) -> tuple[int, ...] | None:
    matches = VER_RE.findall(text)
    if not matches:
        return None
    parts = re.split(r"[._]", matches[-1])
    nums = tuple(int(x) for x in parts if x.isdigit())
    return nums or None


def version_str(v: tuple[int, ...]) -> str:
    return "v" + ".".join(str(x) for x in v)


def _should_skip_path(path: Path) -> bool:
    return bool(set(path.parts) & SKIP_DIR_NAMES)


def _is_pack_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if any((path / name).is_file() for name in PACK_MARKER_NAMES):
        return True
    try:
        for child in path.iterdir():
            if not child.is_file():
                continue
            name = child.name
            if name.startswith("README") and name.endswith(".md"):
                return True
            if name.startswith("routeB_RT_bem") and name.endswith(".py"):
                return True
    except OSError:
        return False
    return False


def _match_glob(name: str, pattern: str) -> bool:
    return fnmatch.fnmatch(name.lower(), pattern.lower())


def _is_reparse_point(path: Path) -> bool:
    """True for a Windows junction or symlink.

    The SP02 compatibility layer puts ~50 junctions at the repo root, each pointing
    back into the catalog. A plain rglob descends through every one of them and
    re-walks the whole tree once per junction, which took pack discovery from under a
    second to ten minutes. Reparse points must be pruned, not merely filtered out of
    the results.
    """
    try:
        attrs = os.stat(path, follow_symlinks=False).st_file_attributes
    except (OSError, AttributeError):
        return path.is_symlink()
    return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT


def _walk_pruned(root: Path):
    """os.walk over root, pruning skip-listed names and reparse points."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIR_NAMES
            and not d.startswith(".")
            and not _is_reparse_point(Path(dirpath) / d)
        ]
        yield Path(dirpath), dirnames, filenames


def _iter_candidate_dirs(root: Path) -> list[Path]:
    found: list[Path] = []
    if not root.is_dir():
        return found
    for dirpath, dirnames, _filenames in _walk_pruned(root):
        for name in dirnames:
            p = dirpath / name
            if _should_skip_path(p):
                continue
            if _is_pack_dir(p):
                found.append(p)
    return found


def _iter_candidate_zips(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for dirpath, _dirnames, filenames in _walk_pruned(root):
        for name in filenames:
            if not name.lower().endswith(".zip"):
                continue
            z = dirpath / name
            if not _should_skip_path(z):
                out.append(z)
    return out


def resolve_pack(
    pack_glob: str,
    *,
    wb: Path = WB,
    restore: Path = RESTORE,
    pack_path_hint: str | None = None,
    index: PackIndex | None = None,
) -> ResolvedPack | None:
    """Return highest semver match for pack_glob across working trees and archives."""
    idx = index or get_pack_index(wb=wb, restore=restore)
    best_dir: tuple[tuple[int, ...], Path] | None = None
    best_zip: tuple[tuple[int, ...], Path] | None = None

    if pack_path_hint:
        hint = wb / pack_path_hint
        if hint.is_dir() and _is_pack_dir(hint):
            ver = parse_version(hint.name) or (0,)
            best_dir = (ver, hint)

    for name, ver, p in idx.dirs:
        if not _match_glob(name, pack_glob):
            continue
        if best_dir is None or ver > best_dir[0]:
            best_dir = (ver, p)

    for name, ver, z in idx.zips:
        if not _match_glob(name, pack_glob):
            continue
        if best_zip is None or ver > best_zip[0]:
            best_zip = (ver, z)

    if best_dir is None and best_zip is None:
        return None

    if best_dir and best_zip:
        ver = max(best_dir[0], best_zip[0])
    elif best_dir:
        ver = best_dir[0]
    else:
        assert best_zip is not None
        ver = best_zip[0]

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(wb)).replace("\\", "/")
        except ValueError:
            return str(p).replace("\\", "/")

    working = _rel(best_dir[1]) if best_dir and best_dir[0] == ver else None
    if working is None and best_dir and best_dir[0] >= ver:
        working = _rel(best_dir[1])
    archive = _rel(best_zip[1]) if best_zip and best_zip[0] == ver else None
    if archive is None and best_zip and best_zip[0] >= ver:
        archive = _rel(best_zip[1])

    # Prefer working tree version label when both exist
    label_ver = best_dir[0] if best_dir else ver
    if best_zip and best_zip[0] > (best_dir[0] if best_dir else (0,)):
        label_ver = best_zip[0]

    return ResolvedPack(
        version=label_ver,
        version_str=version_str(label_ver),
        working_tree=working,
        archive_zip=archive,
    )


def load_registry(path: Path | None = None) -> dict[str, Any]:
    path = path or DEFAULT_REGISTRY
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"registry root must be mapping: {path}")
    return data


def _entry_from_raw(raw: dict[str, Any]) -> RegistryEntry:
    ht = raw.get("hypothesis_table")
    return RegistryEntry(
        id=str(raw["id"]),
        family=str(raw["family"]),
        name=str(raw["name"]),
        pack_glob=str(raw["pack_glob"]),
        hypothesis=str(raw.get("hypothesis") or ""),
        blind=bool(raw.get("blind", False)),
        h0=str(raw.get("h0") or ""),
        h1=str(raw.get("h1") or ""),
        dataset=str(raw.get("dataset") or ""),
        gate=str(raw.get("gate") or ""),
        physics_status=str(raw.get("physics_status") or "UNTESTED").upper(),
        numerics_status=str(raw.get("numerics_status") or "NOT_RUN").upper(),
        result_sha256=raw.get("result_sha256"),
        next_test=str(raw.get("next_test") or ""),
        hypothesis_table=int(ht) if ht is not None else None,
        stars=str(raw.get("stars") or ""),
        physics_emoji=str(raw.get("physics_emoji") or ""),
        question=str(raw.get("question") or ""),
        pack_path_hint=raw.get("pack_path_hint"),
    )


def load_entries(path: Path | None = None, *, resolve: bool = True) -> list[RegistryEntry]:
    data = load_registry(path)
    raw_entries = data.get("entries") or []
    entries = [_entry_from_raw(r) for r in raw_entries]
    if resolve:
        index = get_pack_index()
        for e in entries:
            e.resolved = resolve_pack(
                e.pack_glob, pack_path_hint=e.pack_path_hint, index=index
            )
    return entries


def validate_registry(data: dict[str, Any] | None = None, path: Path | None = None) -> list[str]:
    if data is None:
        data = load_registry(path)
    errors: list[str] = []
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    seen_ht: set[int] = set()
    families_seen: set[str] = set()

    for i, raw in enumerate(entries):
        prefix = f"entries[{i}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix}: must be mapping")
            continue
        for key in ("id", "family", "name", "pack_glob"):
            if key not in raw:
                errors.append(f"{prefix}: missing {key}")
        eid = raw.get("id")
        if eid in seen_ids:
            errors.append(f"{prefix}: duplicate id {eid!r}")
        elif isinstance(eid, str):
            seen_ids.add(eid)

        fam = raw.get("family")
        if fam not in FAMILIES:
            errors.append(f"{prefix}: invalid family {fam!r}")
        else:
            families_seen.add(str(fam))

        ps = str(raw.get("physics_status", "UNTESTED")).upper()
        if ps not in PHYSICS_STATUSES:
            errors.append(f"{prefix}: invalid physics_status {ps!r}")

        ns = str(raw.get("numerics_status", "NOT_RUN")).upper()
        if ns not in NUMERICS_STATUSES:
            errors.append(f"{prefix}: invalid numerics_status {ns!r}")

        ht = raw.get("hypothesis_table")
        if ht is not None:
            ht_int = int(ht)
            if ht_int in seen_ht:
                errors.append(f"{prefix}: duplicate hypothesis_table {ht_int}")
            seen_ht.add(ht_int)

    for fam in FAMILIES:
        if fam not in families_seen:
            errors.append(f"no entries for family {fam}")

    return errors


def discover_unregistered(
    entries: list[RegistryEntry] | None = None,
    *,
    wb: Path = WB,
    index: PackIndex | None = None,
) -> list[str]:
    """Pack directory names that look like falsifiers but match no registry glob."""
    if entries is None:
        entries = load_entries(resolve=False)

    patterns = [e.pack_glob for e in entries]
    idx = index or get_pack_index(wb=wb)

    def covered(name: str) -> bool:
        return any(_match_glob(name, pat) for pat in patterns)

    unregistered: list[str] = []
    for name, _ver, p in idx.dirs:
        if not re.search(
            r"Falsifier|falsifier|Harness|harness|Sutcliffe|contact_billiard|"
            r"chiral_kelvin|ideal_links|KnotPlot_3p1|dimensionless|nonfit|"
            r"Einstein_SST|Helmholtz|Kelvin_|routeB|SST21D",
            name,
            re.I,
        ):
            continue
        if not covered(name):
            rel = str(p.relative_to(wb)).replace("\\", "/")
            unregistered.append(rel)
    return sorted(set(unregistered))


def scan_result_sha256(pack_path: Path) -> str | None:
    """Best-effort hash from sealed results under a pack directory."""
    if not pack_path.is_dir():
        return None
    candidates: list[Path] = []
    for name in ("MANIFEST.sha256", "results_manifest.sha256", "SHA256SUMS"):
        candidates.extend(pack_path.rglob(name))
    for manifest in candidates:
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            token = line.split()[0]
            if re.fullmatch(r"[0-9a-fA-F]{64}", token):
                return token.lower()
    # Hash newest results_* directory marker file if present
    result_dirs = sorted(
        (d for d in pack_path.rglob("results_*") if d.is_dir()),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    for rd in result_dirs[:3]:
        for marker in ("REPORT.md", "summary.json", "blind_summary.json"):
            f = rd / marker
            if f.is_file():
                h = hashlib.sha256()
                with f.open("rb") as fp:
                    while block := fp.read(1 << 20):
                        h.update(block)
                return h.hexdigest()
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to falsifier_registry.yaml",
    )
    ap.add_argument(
        "--validate",
        action="store_true",
        help="Validate registry and exit",
    )
    ap.add_argument(
        "--discover",
        action="store_true",
        help="List pack dirs not covered by registry globs",
    )
    args = ap.parse_args(argv)

    if args.validate:
        errs = validate_registry(path=args.registry)
        if errs:
            for e in errs:
                print(e, file=sys.stderr)
            return 1
        print(f"OK: {args.registry}")
        return 0

    if args.discover:
        entries = load_entries(args.registry, resolve=False)
        gaps = discover_unregistered(entries)
        print(f"Unregistered packs: {len(gaps)}")
        for g in gaps:
            print(f"  {g}")
        return 0

    entries = load_entries(args.registry)
    for e in entries:
        ver = e.resolved.version_str if e.resolved else "?"
        print(f"{e.id}\t{e.family}\t{ver}\t{e.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
