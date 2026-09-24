"""Locate the workbench root and frozen A029 sources without patching A029."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def workbench_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "10_docs" / "registry").is_dir() and (parent / "01_research").is_dir():
            return parent
    raise RuntimeError("SST workbench root not found")


def pack_root() -> Path:
    return Path(__file__).resolve().parents[1]


def a029_src() -> Path:
    return (
        workbench_root()
        / "01_research"
        / "A_falsifiers"
        / "A029_finite_core_axial_toroidal_phase_delay"
        / "A029-v0.4.0"
        / "src"
    )


def a029_v020_root() -> Path:
    return (
        workbench_root()
        / "01_research"
        / "A_falsifiers"
        / "A029_finite_core_axial_toroidal_phase_delay"
        / "A029-v0.2.0"
    )


def ensure_a029_import() -> None:
    src = str(a029_src())
    if src not in sys.path:
        sys.path.insert(0, src)


def load_thresholds(path: Path | None = None) -> dict[str, Any]:
    dest = path or (pack_root() / "THRESHOLDS_FROZEN.json")
    return json.loads(dest.read_text(encoding="utf-8"))


def sha256_obj(obj: Any) -> str:
    import hashlib

    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def complex_hash(vector) -> str:
    import hashlib
    import numpy as np

    arr = np.asarray(vector, dtype=complex).ravel()
    payload = []
    for z in arr:
        payload.append(float(z.real))
        payload.append(float(z.imag))
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()
