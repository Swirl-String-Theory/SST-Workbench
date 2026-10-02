from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
import numpy as np

@dataclass(frozen=True)
class IdealAB:
    knot_id: str
    conway: str
    L: float
    D: float
    harmonics: np.ndarray
    A: np.ndarray
    B: np.ndarray

_AB_RE = re.compile(
    r'<AB\s+Id="(?P<id>[^"]+)"\s+Conway="(?P<conway>[^"]*)"\s+L="\s*(?P<L>[-+0-9.eE]+)"\s+D="\s*(?P<D>[-+0-9.eE]+)"[^>]*>(?P<body>.*?)</AB>',
    re.S,
)
_COEFF_RE = re.compile(r'<Coeff\s+I="\s*(\d+)"\s+A="\s*([^"]+)"\s+B="\s*([^"]+)"\s*/>')


def _vec(text: str) -> list[float]:
    vals = [float(v.strip()) for v in text.split(",")]
    if len(vals) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals


def parse_ideal_ab(path: str | Path, knot_id: str = "3:1:1") -> IdealAB:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    selected = None
    for m in _AB_RE.finditer(text):
        if m.group("id") == knot_id:
            selected = m
            break
    if selected is None:
        # allow a file containing only the inside block but malformed surrounding whitespace
        marker = f'<AB Id="{knot_id}"'
        if marker not in text:
            raise KeyError(f"Knot Id={knot_id!r} not found in {path}")
        raise ValueError(f"Could not parse AB block for Id={knot_id!r}")
    hs, aa, bb = [], [], []
    for c in _COEFF_RE.finditer(selected.group("body")):
        hs.append(int(c.group(1)))
        aa.append(_vec(c.group(2)))
        bb.append(_vec(c.group(3)))
    if not hs:
        raise ValueError(f"No Fourier coefficients found for {knot_id}")
    return IdealAB(
        knot_id=knot_id,
        conway=selected.group("conway"),
        L=float(selected.group("L")),
        D=float(selected.group("D")),
        harmonics=np.asarray(hs, dtype=int),
        A=np.asarray(aa, dtype=float),
        B=np.asarray(bb, dtype=float),
    )


def sample_ideal_ab(model: IdealAB, n: int) -> np.ndarray:
    if n < 16:
        raise ValueError("n must be >= 16")
    t = np.linspace(0.0, 2.0 * np.pi, int(n), endpoint=False)
    p = np.zeros((len(t), 3), dtype=float)
    for h, a, b in zip(model.harmonics, model.A, model.B):
        p += np.cos(h * t)[:, None] * a + np.sin(h * t)[:, None] * b
    return p
