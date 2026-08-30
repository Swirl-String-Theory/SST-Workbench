"""Inventory legacy Workbench knot paths without moving files.

Writes Registry/inventory_unmigrated.json with proposed provider_id / class / destination.
Unknown provenance is routed to Quarantine suggestions.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .library_root import find_knot_library_root, require_knot_library_root

DEFAULT_SCAN_RELATIVE = [
    "Ideal_Sources",
    "Ideal_Fremlin_Fseries",
    "KnotPlot/knots",
    "KnotPlot/Knots_FourierSeries",
    "Katlas_Sources_v0.2.2_Outputs",
]

GEOM_EXTS = {".txt", ".xyz", ".csv", ".vect", ".knot", ".kp", ".kpf", ".fseries", ".short", ".gz", ".zip", ".json"}


def _workbench_root(library_root: Path) -> Path:
    # Knot_Library lives directly under SST-Workbench
    return library_root.parent


def classify_legacy_path(path: Path, workbench: Path) -> dict[str, Any]:
    """Propose provider_id, class, and destination under Knot_Library (no moves)."""
    try:
        rel = path.relative_to(workbench).as_posix()
    except ValueError:
        rel = str(path)
    lower = rel.lower().replace("\\", "/")
    name = path.name.lower()
    parts = lower.split("/")

    proposal: dict[str, Any] = {
        "path": str(path),
        "relative_path": rel,
        "provider_id": None,
        "class": None,
        "destination": None,
        "action": "leave",
        "notes": [],
    }

    # Already under Knot_Library/Sources → skip as migrated copy target
    if "knot_library/sources/" in lower:
        proposal["action"] = "already_in_sources"
        proposal["notes"].append("path already under Knot_Library/Sources")
        return proposal

    if "ideal_fremlin_fseries" in lower or ("fremlin" in parts and "ideal_fremlin" in lower):
        proposal.update(
            {
                "provider_id": "fremlin_fourier",
                "class": "original",
                "destination": "Sources/FourierSeries_Fremlin/original",
                "notes": ["Fremlin archive / mirror"],
            }
        )
        return proposal

    if "knotplot/knots_fourierseries" in lower:
        proposal.update(
            {
                "provider_id": "fremlin_fourier",
                "class": "original",
                "destination": "Sources/FourierSeries_Fremlin/original",
                "notes": ["KnotPlot FourierSeries mirror of Fremlin; prefer Ideal_Fremlin_Fseries as canon"],
            }
        )
        return proposal

    if any(p.startswith("ideal") and p.endswith(".gz") for p in [name]) or (
        "ideal_sources" in lower and name.startswith("ideal") and name.endswith(".gz")
    ):
        # Twelve* is Ridgerunner; Ideal*.gz Gilbert
        if name.startswith("twelvedata") or name.startswith("twelvesummary") or name == "0twelvedata.csv":
            proposal.update(
                {
                    "provider_id": "ridgerunner",
                    "class": "original",
                    "destination": "Sources/Ridgerunner_Cantarella_Rawdon/original",
                    "notes": ["Twelve-crossing polyline archive via Knot Atlas"],
                }
            )
        else:
            proposal.update(
                {
                    "provider_id": "gilbert_ideal",
                    "class": "original",
                    "destination": "Sources/Ideal_Gilbert/original",
                    "notes": ["Gilbert Ideal Fourier / IdealLinks gzip"],
                }
            )
        return proposal

    if "ideal_sources" in lower and (
        name.startswith("twelve") or name == "0twelvedata.csv"
    ):
        proposal.update(
            {
                "provider_id": "ridgerunner",
                "class": "original",
                "destination": "Sources/Ridgerunner_Cantarella_Rawdon/original",
                "notes": ["Twelve-crossing polyline archive via Knot Atlas"],
            }
        )
        return proposal

    if "knotplot/knots/final" in lower or lower.endswith("knots/final") or "/knots/final/" in lower:
        proposal.update(
            {
                "provider_id": "knotplot",
                "class": "relaxed",
                "destination": "Sources/KnotPlot_Scharein/SST_Relaxation_Campaigns",
                "notes": ["Shared RR-polished finals — not Database_Original"],
            }
        )
        return proposal

    if "_rr_" in name or name.endswith(".rr") or "/ridgerunner/" in lower:
        proposal.update(
            {
                "provider_id": "ridgerunner",
                "class": "continued" if "_rr_" in name else "unknown",
                "destination": "Sources/Ridgerunner_Cantarella_Rawdon/Continued",
                "notes": ["Ridgerunner pipeline artifact"],
            }
        )
        if "final" in name or name.endswith("_final.txt"):
            proposal["class"] = "final"
            proposal["destination"] = "Sources/Ridgerunner_Cantarella_Rawdon/Final"
        return proposal

    if "knotplot/knots/" in lower and ("_trial_" in name or name.endswith(".kpc")):
        if "_trial_" in name and any(x in name for x in ("ago", "relax")):
            klass, dest = "relaxed", "Sources/KnotPlot_Scharein/Relaxed"
        else:
            klass, dest = "seed", "Sources/KnotPlot_Scharein/Initial_Seeds"
        proposal.update(
            {
                "provider_id": "knotplot",
                "class": klass,
                "destination": dest,
                "notes": ["KnotPlot per-id campaign seed/trial"],
            }
        )
        return proposal

    if "katlas_sources" in lower or "katlas" in parts[:2]:
        proposal.update(
            {
                "provider_id": "katlas",
                "class": "snapshot",
                "destination": "Sources/KAtlas_BarNatan/topology",
                "notes": ["KAtlas export; prefer inventory over blind duplication"],
            }
        )
        return proposal

    # Unknown
    if path.suffix.lower() not in GEOM_EXTS and name not in {"fseries", "ideal", "ideal.txt"}:
        proposal.update(
            {
                "provider_id": None,
                "class": None,
                "destination": "Quarantine/Unknown_Format",
                "notes": ["unrecognized format / extension"],
            }
        )
    else:
        proposal.update(
            {
                "provider_id": None,
                "class": None,
                "destination": "Quarantine/Unknown_Source",
                "notes": ["unknown provenance — do not use in strict falsifiers"],
            }
        )
    return proposal


def inventory_sources(
    *,
    library_root: Path | None = None,
    workbench: Path | None = None,
    scan_relative: Iterable[str] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Scan legacy locations; classify; optionally write Registry/inventory_unmigrated.json.

    Never moves or deletes files.
    """
    root = library_root or require_knot_library_root()
    wb = workbench or _workbench_root(root)
    rels = list(scan_relative or DEFAULT_SCAN_RELATIVE)
    entries: list[dict[str, Any]] = []
    scanned_roots: list[str] = []

    for rel in rels:
        base = wb / rel
        if not base.exists():
            continue
        scanned_roots.append(str(base))
        if base.is_file():
            entries.append(classify_legacy_path(base, wb))
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            # Skip huge / regenerable RR snapshot dumps
            if "snapshots" in path.parts:
                continue
            if path.suffix.lower() == ".pyd" or path.name.endswith(".pyc"):
                continue
            # Limit inventory noise: skip pure image/mesh under Fremlin when scanning whole tree? Keep them.
            entries.append(classify_legacy_path(path, wb))

    report = {
        "schema": "sst-knot-library-inventory/1",
        "library_root": str(root),
        "workbench": str(wb),
        "scanned_roots": scanned_roots,
        "file_count": len(entries),
        "moved": False,
        "action": "inventory_only",
        "counts_by_provider": {},
        "counts_by_destination": {},
        "entries": entries,
    }
    for e in entries:
        pid = e.get("provider_id") or "quarantine"
        report["counts_by_provider"][pid] = report["counts_by_provider"].get(pid, 0) + 1
        dest = e.get("destination") or "none"
        report["counts_by_destination"][dest] = report["counts_by_destination"].get(dest, 0) + 1

    if write:
        out = root / "Registry" / "inventory_unmigrated.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        report["out"] = str(out)
    return report
