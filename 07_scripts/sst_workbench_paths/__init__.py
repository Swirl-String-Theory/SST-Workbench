"""SST Workbench path resolution.

Resolution order for each path: explicit argument, environment variable,
upward search for ``.sst-workbench-root``, then packaged default under the
workbench root. Never use bare ``Path.parents[N]``.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT_MARKER = ".sst-workbench-root"
PATH_MAP_REL = Path("10_docs") / "migration" / "path_map.csv"
CATALOG_INDEX_REL = Path("10_docs") / "registry" / "catalog_index.json"

# Prefer research when the same catalog_id appears in multiple domains.
_DOMAIN_PREF = (
    "01_research",
    "02_libraries",
    "05_apps",
    "04_tools",
    "03_data",
)


class WorkbenchRootNotFound(FileNotFoundError):
    """Raised when ``.sst-workbench-root`` cannot be located."""


def find_workbench_root(
    start: str | Path | None = None,
    *,
    explicit: str | Path | None = None,
) -> Path:
    """Locate the workbench root.

    Order: ``explicit``, ``SST_WORKBENCH_ROOT``, then walk upward from
    ``start`` (default: this file) looking for ``.sst-workbench-root``.
    """
    if explicit is not None:
        p = Path(explicit).expanduser().resolve()
        if not (p / ROOT_MARKER).is_file():
            raise WorkbenchRootNotFound(
                f"explicit root {p} has no {ROOT_MARKER}"
            )
        return p

    env = os.environ.get("SST_WORKBENCH_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / ROOT_MARKER).is_file():
            return p
        # Env is authoritative when set even without marker (migration / CI),
        # but only if the path exists as a directory.
        if p.is_dir():
            return p
        raise WorkbenchRootNotFound(
            f"SST_WORKBENCH_ROOT={env!r} is not an existing directory"
        )

    # When ``start`` is given, only walk from that path (testable isolation;
    # missing marker must raise rather than silently discovering via __file__).
    if start is not None:
        bases = [Path(start).expanduser().resolve()]
    else:
        bases = [Path(__file__).resolve(), Path.cwd().resolve()]

    seen: set[Path] = set()
    for base in bases:
        cur = base if base.is_dir() else base.parent
        for p in [cur, *cur.parents]:
            if p in seen:
                continue
            seen.add(p)
            if (p / ROOT_MARKER).is_file():
                return p

    raise WorkbenchRootNotFound(
        f"Could not find {ROOT_MARKER}. Set SST_WORKBENCH_ROOT or run from "
        "inside the SST-Workbench tree."
    )


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name)
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def _prefer_existing(*candidates: Path) -> Path:
    """Return the first existing candidate, else the first candidate."""
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def workbench_root(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    return find_workbench_root(start=start, explicit=explicit)


def data_root(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if (env := _env_path("SST_DATA_ROOT")) is not None:
        return env
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    return workbench_root(start=start) / "03_data"


def knot_dataset(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if (env := _env_path("SST_KNOT_DATASET")) is not None:
        return env
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    root = workbench_root(start=start)
    data = data_root(start=start)
    return _prefer_existing(
        data / "A_knots" / "04_knotplot" / "final",
        root / "KnotPlot" / "knots" / "final",
    )


def ideal_sources(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if (env := _env_path("SST_IDEAL_SOURCES")) is not None:
        return env
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    root = workbench_root(start=start)
    data = data_root(start=start)
    return _prefer_existing(
        data / "A_knots" / "01_ideal" / "ideal_sources",
        root / "Ideal_Sources",
    )


def katlas_sources(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if (env := _env_path("SST_KATLAS_SOURCES")) is not None:
        return env
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    root = workbench_root(start=start)
    data = data_root(start=start)
    return _prefer_existing(
        data / "A_knots" / "03_katlas" / "v0.2.2",
        root / "Katlas_Sources_v0.2.2_Outputs",
    )


def fseries_root(
    *,
    start: str | Path | None = None,
    explicit: str | Path | None = None,
) -> Path:
    if (env := _env_path("SST_FSERIES_ROOT")) is not None:
        return env
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    root = workbench_root(start=start)
    data = data_root(start=start)
    return _prefer_existing(
        data / "A_knots" / "02_fourier" / "knotplot_legacy",
        root / "KnotPlot" / "Knots_FourierSeries",
        root / "Fremlin_FourierSeries",
    )


def _load_path_map(root: Path) -> list[dict[str, str]]:
    path = root / PATH_MAP_REL
    if not path.is_file():
        raise FileNotFoundError(f"path_map.csv not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_catalog_index(root: Path) -> dict | None:
    path = root / CATALOG_INDEX_REL
    if not path.is_file():
        return None
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _family_from_catalog_index(
    index: dict, catalog_id: str, *, domain: str | None
) -> Path | None:
    """Read ``by_domain[domain][catalog_id].path`` from catalog_index.json."""
    by_domain = index.get("by_domain")
    if isinstance(by_domain, dict):
        if domain:
            domains = [domain] if domain in by_domain else []
        else:
            domains = [d for d in _DOMAIN_PREF if d in by_domain]
            domains += [d for d in by_domain if d not in domains]
        for d in domains:
            bucket = by_domain.get(d) or {}
            if not isinstance(bucket, dict):
                continue
            item = bucket.get(catalog_id)
            if isinstance(item, dict):
                rel = item.get("path")
                if rel:
                    return Path(rel)

    entries = index.get("by_id")
    candidates: list[dict] = []
    if isinstance(entries, dict) and catalog_id in entries:
        item = entries[catalog_id]
        if isinstance(item, dict):
            candidates.append(item)
        elif isinstance(item, list):
            candidates.extend(item)
    elif isinstance(entries, list):
        for item in entries:
            if isinstance(item, dict) and item.get("catalog_id") == catalog_id:
                candidates.append(item)
    if domain:
        candidates = [
            c
            for c in candidates
            if c.get("domain") == domain
            or str(c.get("path") or c.get("target_family") or "").startswith(
                domain
            )
        ]
    if not candidates:
        return None
    c0 = candidates[0]
    rel = c0.get("path") or c0.get("target_family") or c0.get("new_path")
    if not rel:
        return None
    return Path(rel)


def _pick_path_map_row(
    rows: list[dict[str, str]],
    catalog_id: str,
    *,
    domain: str | None,
) -> dict[str, str]:
    matches = [
        r
        for r in rows
        if (r.get("catalog_id") or "").strip() == catalog_id
        and (r.get("status") or "") != "skipped"
    ]
    if domain:
        matches = [r for r in matches if (r.get("domain") or "") == domain]
    if not matches:
        raise KeyError(f"unknown catalog_id: {catalog_id!r}")

    def sort_key(r: dict[str, str]) -> tuple:
        dom = r.get("domain") or ""
        try:
            pref = _DOMAIN_PREF.index(dom)
        except ValueError:
            pref = len(_DOMAIN_PREF)
        new = (r.get("new_path") or "").replace("\\", "/")
        # Prefer family roots (path ends with _{slug} containing the id)
        leaf = new.rstrip("/").split("/")[-1]
        is_family = leaf.startswith(f"{catalog_id}_") or leaf == catalog_id
        return (pref, 0 if is_family else 1, len(new), new)

    matches.sort(key=sort_key)
    return matches[0]


def resolve_family(
    catalog_id: str,
    version: str | None = None,
    *,
    domain: str | None = None,
    start: str | Path | None = None,
) -> Path:
    """Resolve a catalog family directory (and optional version subdirectory).

    Until SP08's catalog index exists, uses ``path_map.csv``. Prefers the
    destination path when it exists on disk, otherwise the still-present
    ``old_path`` (pre-move / junction era).
    """
    cid = (catalog_id or "").strip()
    if not cid:
        raise KeyError("catalog_id must be non-empty")

    root = workbench_root(start=start)

    index = _load_catalog_index(root)
    if index is not None:
        rel = _family_from_catalog_index(index, cid, domain=domain)
        if rel is not None:
            family = (root / rel).resolve() if not rel.is_absolute() else rel
            return _with_version(family, version)

    row = _pick_path_map_row(_load_path_map(root), cid, domain=domain)
    new_rel = (row.get("new_path") or "").replace("\\", "/").strip()
    old_rel = (row.get("old_path") or "").replace("\\", "/").strip()
    new_path = (root / new_rel).resolve() if new_rel else None
    old_path = (root / old_rel).resolve() if old_rel else None

    if new_path and new_path.exists():
        family = new_path
    elif old_path and old_path.exists():
        family = old_path
    elif new_path is not None:
        family = new_path
    elif old_path is not None:
        family = old_path
    else:
        raise KeyError(f"no path mapped for catalog_id={cid!r}")

    return _with_version(family, version)


def _with_version(family: Path, version: str | None) -> Path:
    if not version:
        return family
    ver = version.strip()
    # Accept both "v0.1.1" and bare keys already stored as directory names.
    direct = family / ver
    if direct.exists():
        return direct
    # Fuzzy: any child whose name contains the version token.
    if family.is_dir():
        hits = [
            p
            for p in family.iterdir()
            if p.is_dir() and ver in p.name
        ]
        if len(hits) == 1:
            return hits[0]
        if hits:
            # Prefer exact suffix match
            exact = [p for p in hits if p.name.endswith(ver) or p.name == ver]
            if len(exact) == 1:
                return exact[0]
            raise FileNotFoundError(
                f"ambiguous version {ver!r} under {family}: "
                + ", ".join(p.name for p in hits[:5])
            )
    return direct


# Plan-facing aliases (recomputed on each attribute access so env overrides work).
def __getattr__(name: str):
    mapping = {
        "WORKBENCH_ROOT": workbench_root,
        "DATA_ROOT": data_root,
        "KNOT_DATASET": knot_dataset,
        "IDEAL_SOURCES": ideal_sources,
        "KATLAS_SOURCES": katlas_sources,
        "FSERIES_ROOT": fseries_root,
    }
    if name in mapping:
        return mapping[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ROOT_MARKER",
    "WorkbenchRootNotFound",
    "find_workbench_root",
    "workbench_root",
    "data_root",
    "knot_dataset",
    "ideal_sources",
    "katlas_sources",
    "fseries_root",
    "resolve_family",
    "WORKBENCH_ROOT",
    "DATA_ROOT",
    "KNOT_DATASET",
    "IDEAL_SOURCES",
    "KATLAS_SOURCES",
    "FSERIES_ROOT",
]
