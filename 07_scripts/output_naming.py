"""SP09: output artifact names come from metadata, never from the version directory.

A run from ``A042-v0.1.1/`` must still produce
``SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs/``.
``project.json`` ``legacy_dir`` is the pre-rename folder name and is byte-identical
to the historical stem. Fall back to the directory name for packs that have no
metadata yet (tests, templates).
"""
from __future__ import annotations

import json
from pathlib import Path


def artifact_stem(version_dir: Path) -> str:
    """Stem used for ``{stem}-outputs/`` and ``{stem}_outputs.zip``."""
    version_dir = Path(version_dir)
    pj = version_dir / "project.json"
    if pj.is_file():
        try:
            legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
        except (OSError, json.JSONDecodeError):
            legacy = ""
        if legacy:
            return legacy
    return version_dir.name


def outputs_dir_name(version_dir: Path) -> str:
    return f"{artifact_stem(version_dir)}-outputs"


def outputs_zip_name(version_dir: Path) -> str:
    return f"{artifact_stem(version_dir)}_outputs.zip"
