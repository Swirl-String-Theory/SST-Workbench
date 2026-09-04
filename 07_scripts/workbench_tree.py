"""Build a folder-map JSON of SST-Workbench: family -> versions / subfolders + dates."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[1]
DEFAULT_OUT = WB / "INVENTORY_TREE.json"

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".tmp.driveupload",
        "site-packages",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".idea",
        ".cursor",
    }
)

# Counts only -- expanding these would dump thousands of data dirs into the map.
OPAQUE_NAMES = frozenset(
    {
        "knots",
        "out",
        "outputs",
        "build",
        "dist",
        "htmlcov",
        "ridgerunner",
    }
)

# List immediate children as leaves (theme buckets, media roots), then stop.
SHALLOW_NAMES = frozenset({"Restore_Archives", "media"})

VER_TOKEN_RE = re.compile(r"(?i)(?<![A-Za-z0-9])(v\d[\w.-]*)")
VER_NUMS_RE = re.compile(r"v(\d+(?:[._]\d+)*)", re.I)


def parse_version_tuple(text: str) -> tuple[int, ...] | None:
    matches = VER_NUMS_RE.findall(text)
    if not matches:
        return None
    parts = re.split(r"[._]", matches[-1])
    nums = tuple(int(x) for x in parts if x.isdigit())
    return nums or None


def version_token(name: str) -> str | None:
    match = VER_TOKEN_RE.search(name)
    if not match:
        return None
    token = match.group(1)
    token = token.rstrip("._-")
    return token if token else None


def is_version_dir_name(name: str) -> bool:
    return version_token(name) is not None


def iso_from_timestamp(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def folder_dates(path: Path) -> dict[str, str]:
    st = path.stat()
    created_ts = getattr(st, "st_birthtime", None)
    if created_ts is None:
        created_ts = st.st_ctime
    return {
        "created": iso_from_timestamp(float(created_ts)),
        "modified": iso_from_timestamp(st.st_mtime),
    }


def _unique_version_key(name: str, used: set[str]) -> str:
    token = version_token(name)
    if token and token not in used:
        return token
    return name


def _should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES or name.startswith(".")


def _child_counts(path: Path) -> tuple[int, int]:
    n_dirs = 0
    n_files = 0
    try:
        for child in path.iterdir():
            if child.is_dir():
                if not _should_skip_dir(child.name):
                    n_dirs += 1
            elif child.is_file():
                n_files += 1
    except OSError:
        return 0, 0
    return n_dirs, n_files


def _list_dirs(path: Path) -> list[Path]:
    try:
        children = [p for p in path.iterdir() if p.is_dir() and not _should_skip_dir(p.name)]
    except OSError:
        return []
    return sorted(children, key=lambda p: p.name.lower())


def _leaf_entry(path: Path, *, rel: str) -> dict[str, Any]:
    n_dirs, n_files = _child_counts(path)
    entry: dict[str, Any] = {
        "path": rel.replace("\\", "/"),
        **folder_dates(path),
        "dir_count": n_dirs,
        "file_count": n_files,
    }
    return entry


def _latest_version_key(versions: dict[str, dict[str, Any]]) -> str | None:
    if not versions:
        return None

    def sort_key(item: tuple[str, dict[str, Any]]) -> tuple:
        key, meta = item
        name = str(meta.get("name") or key)
        ver = parse_version_tuple(name) or parse_version_tuple(key) or ()
        modified = str(meta.get("modified") or "")
        return (ver, modified, name)

    return max(versions.items(), key=sort_key)[0]


def scan_family(
    path: Path,
    *,
    root: Path,
    depth: int,
    max_depth: int,
) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    node = _leaf_entry(path, rel=rel)
    if depth >= max_depth or path.name in OPAQUE_NAMES:
        return node

    versions: dict[str, dict[str, Any]] = {}
    folders: dict[str, dict[str, Any]] = {}
    used_keys: set[str] = set()
    shallow = path.name in SHALLOW_NAMES

    for child in _list_dirs(path):
        child_rel = child.relative_to(root).as_posix()
        if not shallow and is_version_dir_name(child.name):
            key = _unique_version_key(child.name, used_keys)
            used_keys.add(key)
            versions[key] = {
                "name": child.name,
                **_leaf_entry(child, rel=child_rel),
            }
            continue
        if shallow:
            folders[child.name] = _leaf_entry(child, rel=child_rel)
            continue
        folders[child.name] = scan_family(
            child, root=root, depth=depth + 1, max_depth=max_depth
        )

    if versions:
        node["versions"] = dict(
            sorted(
                versions.items(),
                key=lambda kv: (
                    parse_version_tuple(str(kv[1].get("name") or kv[0])) or (),
                    kv[0].lower(),
                ),
            )
        )
        latest = _latest_version_key(node["versions"])
        if latest is not None:
            node["latest"] = latest
    if folders:
        node["folders"] = folders
    return node


def scan_workbench(root: Path, *, max_depth: int = 3) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    for child in _list_dirs(root):
        tree[child.name] = scan_family(
            child, root=root, depth=1, max_depth=max_depth
        )
    return tree


def build_inventory(
    root: Path,
    *,
    max_depth: int = 3,
) -> dict[str, Any]:
    tree = scan_workbench(root, max_depth=max_depth)
    n_families = len(tree)
    n_versions = 0
    for node in tree.values():
        n_versions += _count_versions(node)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root.resolve()),
        "max_depth": max_depth,
        "family_count": n_families,
        "version_count": n_versions,
        "note": (
            "Map of SST-Workbench folders. Each top-level family lists version "
            "directories (short key when unique) and other subfolders. "
            "created is filesystem birth time (Windows) or ctime; modified is mtime. "
            "Dates follow this machine's copy, not original authoring. "
            "Version pack internals and heavy data trees are not expanded."
        ),
        "tree": tree,
    }


def _count_versions(node: dict[str, Any]) -> int:
    n = len(node.get("versions") or {})
    for child in (node.get("folders") or {}).values():
        n += _count_versions(child)
    return n


def write_inventory(
    payload: dict[str, Any],
    out: Path,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write INVENTORY_TREE.json (family -> versions / folders + dates)."
    )
    parser.add_argument("--root", type=Path, default=WB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-depth", type=int, default=3)
    args = parser.parse_args(argv)
    payload = build_inventory(args.root, max_depth=args.max_depth)
    written = write_inventory(payload, args.out)
    print(
        f"Wrote {written} "
        f"({payload['family_count']} families, {payload['version_count']} versions)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
