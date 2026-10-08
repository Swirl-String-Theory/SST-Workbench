from __future__ import annotations
from pathlib import Path
import hashlib
import numpy as np


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_centerline(path: str | Path) -> list[np.ndarray]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    comps: list[np.ndarray] = []
    cur: list[list[float]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if cur:
                comps.append(np.asarray(cur, dtype=np.float64))
                cur = []
            continue
        if s.startswith("#"):
            continue
        parts = s.replace(",", " ").split()
        vals: list[float] = []
        for token in parts:
            try:
                vals.append(float(token))
            except ValueError:
                break
        if len(vals) >= 3:
            cur.append(vals[:3])
    if cur:
        comps.append(np.asarray(cur, dtype=np.float64))

    out: list[np.ndarray] = []
    for p in comps:
        scale = max(1.0, float(np.ptp(p, axis=0).max()))
        if len(p) > 3 and np.linalg.norm(p[0] - p[-1]) < 1e-12 * scale:
            p = p[:-1]
        if len(p) >= 3:
            out.append(np.ascontiguousarray(p, dtype=np.float64))
    if not out:
        raise ValueError(f"no XYZ components found in {path}")
    return out
