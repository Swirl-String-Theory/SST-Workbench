"""Discover Knot_Library root and resolve provider provenance from SOURCE.json.

Software never parses directory names for provider identity. Machine IDs come from
Registry/providers.json and per-provider SOURCE.json files.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

SOURCE_SCHEMA = "sst-knot-library-source/1"
PROVIDERS_SCHEMA = "sst-knot-library-providers/1"

# Fallback when a path sits outside Sources/ (inventory / quarantine classification only).
HEURISTIC_FAMILY_TO_QUARANTINE = {
    "ideal_txt": "Unknown_Source",
    "knotplot_fseries": "Unknown_Source",
    "ridgerunner": "Unknown_Source",
    "vect": "Unknown_Format",
    "knotplot_binary": "Unknown_Source",
    "coordinate_file": "Unknown_Format",
}


def _is_knot_library_root(path: Path) -> bool:
    return (path / "Sources").is_dir() and (path / "Registry").is_dir()


def find_knot_library_root(start: str | Path | None = None) -> Path | None:
    """Locate Knot_Library via env, explicit start, or parents of CWD/package."""
    env = os.environ.get("SST_KNOT_LIBRARY_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if _is_knot_library_root(p):
            return p
    candidates: list[Path] = []
    if start is not None:
        candidates.append(Path(start).resolve())
    candidates.append(Path.cwd().resolve())
    # package: .../Knot_Library/SST_Knot_Library/SST_Knot_Library_v0.2.0/sst_knotlib
    pkg = Path(__file__).resolve()
    candidates.extend(pkg.parents)
    seen: set[Path] = set()
    for base in candidates:
        for p in [base, *base.parents]:
            if p in seen:
                continue
            seen.add(p)
            if _is_knot_library_root(p):
                return p
            # Common layout: .../Knot_Library/SST_Knot_Library/<version>/
            sibling = p / "Knot_Library"
            if _is_knot_library_root(sibling):
                return sibling
    return None


def require_knot_library_root(start: str | Path | None = None) -> Path:
    root = find_knot_library_root(start)
    if root is None:
        raise FileNotFoundError(
            "Knot_Library root not found. Set SST_KNOT_LIBRARY_ROOT or run from Workbench."
        )
    return root


def sources_root(library_root: Path | None = None) -> Path:
    root = library_root or require_knot_library_root()
    return root / "Sources"


def load_providers(library_root: Path | None = None) -> dict[str, Any]:
    root = library_root or require_knot_library_root()
    path = root / "Registry" / "providers.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != PROVIDERS_SCHEMA:
        raise ValueError(f"unexpected providers schema: {data.get('schema')}")
    return data


def load_source_json(provider_dir: Path) -> dict[str, Any]:
    path = provider_dir / "SOURCE.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SOURCE_SCHEMA:
        raise ValueError(f"unexpected SOURCE.json schema in {path}: {data.get('schema')}")
    return data


def _provider_dirs(library_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    sources = library_root / "Sources"
    out: list[tuple[Path, dict[str, Any]]] = []
    if not sources.is_dir():
        return out
    for child in sorted(sources.iterdir()):
        if child.is_dir() and (child / "SOURCE.json").is_file():
            out.append((child.resolve(), load_source_json(child)))
    return out


def resolve_path_provenance(path: str | Path, library_root: Path | None = None) -> dict[str, Any]:
    """Resolve provider provenance for a geometry path.

    Returns provider_id/provider_name/class from the nearest Sources/<Provider>/SOURCE.json.
    Paths outside Sources get provider_id=None and a quarantine_hint (never CERTIFIED).
    """
    path = Path(path).resolve()
    root = library_root or find_knot_library_root(path)
    result: dict[str, Any] = {
        "provider_id": None,
        "provider_name": None,
        "class": None,
        "directory": None,
        "construction_objective": None,
        "source_json": None,
        "library_root": str(root) if root else None,
        "quarantine_hint": None,
        "resolved_from": None,
    }
    if root is None:
        result["quarantine_hint"] = "Unknown_Source"
        result["resolved_from"] = "no_library_root"
        return result

    # Prefer longest matching provider directory prefix under Sources/
    best: tuple[Path, dict[str, Any]] | None = None
    for pdir, meta in _provider_dirs(root):
        try:
            path.relative_to(pdir)
        except ValueError:
            continue
        if best is None or len(pdir.parts) > len(best[0].parts):
            best = (pdir, meta)
    if best is not None:
        pdir, meta = best
        sample_class = meta.get("class")
        # Subdirectory class overrides when CLASS.json present
        for parent in [path.parent, *path.parents]:
            class_json = parent / "CLASS.json"
            if class_json.is_file():
                try:
                    cj = json.loads(class_json.read_text(encoding="utf-8"))
                    if cj.get("provider_id") == meta.get("provider_id") and cj.get("class"):
                        sample_class = cj["class"]
                        break
                except (json.JSONDecodeError, OSError):
                    pass
            if parent == pdir:
                break
            # Infer class from known KnotPlot / Ridgerunner subfolder names
            name = parent.name
            if meta.get("provider_id") == "knotplot":
                mapping = {
                    "Database_Original": "original",
                    "Initial_Seeds": "seed",
                    "Relaxed": "relaxed",
                    "Fourier_Exports": "export",
                    "VECT_Exports": "export",
                    "SST_Relaxation_Campaigns": "relaxed",
                }
                if name in mapping:
                    sample_class = mapping[name]
                    break
            if meta.get("provider_id") == "ridgerunner":
                mapping = {
                    "original": "original",
                    "Seeds": "seed",
                    "N0600": "N0600",
                    "N1200": "N1200",
                    "Continued": "continued",
                    "NearIdeal": "near_ideal",
                    "Final": "final",
                }
                if name in mapping:
                    sample_class = mapping[name]
                    break
            if name in {"original", "extracted", "snapshot"}:
                sample_class = name
                break
        result.update(
            {
                "provider_id": meta.get("provider_id"),
                "provider_name": meta.get("provider_name"),
                "class": sample_class,
                "directory": meta.get("directory"),
                "construction_objective": meta.get("construction_objective"),
                "source_json": str(pdir / "SOURCE.json"),
                "resolved_from": "source_json",
            }
        )
        return result

    # Outside Sources → quarantine hint only
    try:
        path.relative_to(root / "Quarantine")
        result["quarantine_hint"] = path.relative_to(root / "Quarantine").parts[0] if path != root / "Quarantine" else "Unknown_Source"
        result["resolved_from"] = "quarantine_path"
    except ValueError:
        result["quarantine_hint"] = "Unknown_Source"
        result["resolved_from"] = "outside_sources"
    return result


@lru_cache(maxsize=1)
def provider_id_directory_map(library_root_str: str | None = None) -> dict[str, str]:
    root = Path(library_root_str) if library_root_str else require_knot_library_root()
    data = load_providers(root)
    return {pid: meta["directory"] for pid, meta in data["providers"].items()}
