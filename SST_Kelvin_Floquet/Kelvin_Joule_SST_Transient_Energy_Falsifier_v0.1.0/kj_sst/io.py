from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any
import numpy as np
from .geometry import clean_curve, curve_length, radius_of_gyration

SUPPORTED = {".txt", ".xyz", ".csv", ".dat", ".pts", ".vect", ".npy", ".json"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_numeric_text(path: Path) -> np.ndarray:
    rows = []
    number = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip() or line.lstrip().startswith(("#", ";", "//")):
            continue
        vals = [float(x) for x in number.findall(line)]
        if len(vals) >= 3:
            rows.append(vals[:3])
    if len(rows) < 8:
        raise ValueError("not enough XYZ-like rows")
    return np.asarray(rows, float)


def _load_vect(path: Path) -> np.ndarray:
    text = path.read_text(encoding="utf-8", errors="ignore").split()
    if not text or text[0].upper() != "VECT":
        raise ValueError("not a VECT file")
    # VECT: ncomp nvertices ncolors; per-component vertex counts; color counts; then vertices.
    idx = 1
    ncomp, nvert, _ncolors = map(int, text[idx:idx+3]); idx += 3
    counts = list(map(int, text[idx:idx+ncomp])); idx += ncomp
    idx += ncomp  # color counts
    if ncomp < 1 or nvert < 8:
        raise ValueError("VECT contains no usable curve")
    first_n = abs(counts[0])
    vals = np.asarray(list(map(float, text[idx:idx+3*first_n])), float).reshape(-1, 3)
    return vals


def load_curve(path: Path) -> np.ndarray:
    ext = path.suffix.lower()
    if ext == ".npy":
        p = np.load(path)
    elif ext == ".json":
        obj: Any = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            obj = obj.get("points", obj.get("curve", obj.get("xyz")))
        p = np.asarray(obj, float)
    elif ext == ".vect":
        p = _load_vect(path)
    else:
        p = _load_numeric_text(path)
    return clean_curve(p)


def discover_curves(dataset: str | Path) -> tuple[list[tuple[Path, np.ndarray]], list[dict]]:
    root = Path(dataset).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"dataset does not exist: {root}")
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED]
    curves, skipped = [], []
    for p in sorted(files):
        try:
            c = load_curve(p)
            curves.append((p, c))
        except Exception as exc:
            skipped.append({"path": str(p.relative_to(root)), "reason": str(exc)})
    return curves, skipped


def curve_metadata(p: np.ndarray) -> dict:
    return {"n_points": int(len(p)), "length_input": curve_length(p), "rg_input": radius_of_gyration(p)}
