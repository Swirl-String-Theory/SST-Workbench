from __future__ import annotations

import gzip
import hashlib
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from .constants import R_C

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDEAL_KNOTS = _PACKAGE_ROOT / "data" / "Ideal.txt.gz"
DEFAULT_IDEAL_LINKS = _PACKAGE_ROOT / "data" / "IdealLinks.txt.gz"

_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
_COEFF_RE = re.compile(
    r'<Coeff\s+I="\s*(\d+)"\s+A="\s*([^"]+)"\s+B="\s*([^"]+)"\s*/>'
)
_AB_RE = re.compile(r'<AB\s+([^>]*\bId="[^"]+"[^>]*)>(.*?)</AB>', re.S)
_TL_RE = re.compile(r'<TL\s+([^>]*\bId="[^"]+"[^>]*)>(.*?)</TL>', re.S)
_STRING_RE = re.compile(r'<STRING\s+([^>]*)>(.*?)</STRING>', re.S)


def _read_text(path: str | Path) -> str:
    p = Path(path)
    if p.suffix.lower() == ".gz":
        with gzip.open(p, "rt", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    return p.read_text(encoding="utf-8", errors="replace")


def _attrs(s: str) -> dict[str, str]:
    return {k: v.strip() for k, v in _ATTR_RE.findall(s)}


def _vec(s: str) -> np.ndarray:
    a = np.fromstring(s, sep=",", dtype=float)
    if a.shape != (3,):
        raise ValueError(f"Expected 3-vector, got {s!r}")
    return a


def _coeffs(body: str) -> list[tuple[int, np.ndarray, np.ndarray]]:
    out: list[tuple[int, np.ndarray, np.ndarray]] = []
    for m in _COEFF_RE.finditer(body):
        out.append((int(m.group(1)), _vec(m.group(2)), _vec(m.group(3))))
    if not out:
        raise ValueError("No Fourier coefficients found")
    return out


def sample_fourier(coeffs: list[tuple[int, np.ndarray, np.ndarray]], samples: int) -> np.ndarray:
    """Sample Gilbert's X(t)=A[0]/2 + sum_i A[i]cos(it)+B[i]sin(it)."""
    n = int(samples)
    if n < 8:
        raise ValueError("samples must be >= 8")
    t = (2.0 * math.pi / n) * np.arange(n, dtype=float)
    pts = np.zeros((n, 3), dtype=float)
    for i, A, B in coeffs:
        if i == 0:
            pts += 0.5 * A
        else:
            pts += np.cos(i * t)[:, None] * A + np.sin(i * t)[:, None] * B
    return pts


def polyline_length(points: np.ndarray) -> float:
    p = np.asarray(points, dtype=float)
    return float(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum())


def _scale_factor(diameter_native: float, scale_mode: str, core_radius: float) -> float:
    mode = scale_mode.lower().replace("-", "_")
    if mode in {"native", "database"}:
        return 1.0
    if mode in {"sst_core", "core", "core_radius"}:
        if diameter_native <= 0:
            raise ValueError("Database diameter D must be positive")
        # Gilbert uses tube DIAMETER D=1. Map it to SST core diameter 2*r_c.
        return (2.0 * float(core_radius)) / float(diameter_native)
    raise ValueError("scale_mode must be 'native' or 'sst_core'")


def list_knot_ids(path: str | Path = DEFAULT_IDEAL_KNOTS) -> list[str]:
    return [_attrs(m.group(1))["Id"] for m in _AB_RE.finditer(_read_text(path))]


def list_link_ids(path: str | Path = DEFAULT_IDEAL_LINKS) -> list[str]:
    return [_attrs(m.group(1))["Id"] for m in _TL_RE.finditer(_read_text(path))]


def load_knot_record(knot_id: str, path: str | Path = DEFAULT_IDEAL_KNOTS) -> dict[str, Any]:
    text = _read_text(path)
    for m in _AB_RE.finditer(text):
        a = _attrs(m.group(1))
        if a.get("Id") == knot_id:
            coeff = _coeffs(m.group(2))
            return {
                "kind": "knot", "id": knot_id, "conway": a.get("Conway", ""),
                "L": float(a["L"]), "D": float(a.get("D", "1")),
                "curves": [{"index": 1, "L": float(a["L"]), "coeffs": coeff}],
                "source_path": str(Path(path)),
            }
    raise KeyError(f"Knot id {knot_id!r} not found in {path}")


def load_link_record(link_id: str, path: str | Path = DEFAULT_IDEAL_LINKS) -> dict[str, Any]:
    text = _read_text(path)
    for m in _TL_RE.finditer(text):
        a = _attrs(m.group(1))
        if a.get("Id") == link_id:
            curves = []
            for sm in _STRING_RE.finditer(m.group(2)):
                sa = _attrs(sm.group(1))
                curves.append({
                    "index": int(sa["I"]), "L": float(sa["L"]), "coeffs": _coeffs(sm.group(2))
                })
            if not curves:
                raise ValueError(f"Link {link_id} contains no STRING records")
            return {
                "kind": "link", "id": link_id, "conway": a.get("Conway", ""),
                "D": float(a.get("D", "1")), "curves": curves,
                "source_path": str(Path(path)),
            }
    raise KeyError(f"Link id {link_id!r} not found in {path}")


def source_sampling(record: dict[str, Any]) -> int:
    # Database documentation: knots: 512 points; links: 256 for 2/3 strings, 128 for 4/5 strings.
    if record["kind"] == "knot":
        return 512
    return 256 if len(record["curves"]) <= 3 else 128


def sample_record(record: dict[str, Any], samples: int | None = None, *,
                  scale_mode: str = "native", core_radius: float = R_C) -> list[np.ndarray]:
    n = source_sampling(record) if samples is None else int(samples)
    scale = _scale_factor(float(record["D"]), scale_mode, core_radius)
    return [sample_fourier(c["coeffs"], n) * scale for c in record["curves"]]


def gauss_linking_number(a: np.ndarray, b: np.ndarray, *, chunk: int = 128) -> float:
    """Midpoint polygon quadrature of the Gauss linking integral."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    da = np.roll(a, -1, axis=0) - a
    db = np.roll(b, -1, axis=0) - b
    ma = 0.5 * (a + np.roll(a, -1, axis=0))
    mb = 0.5 * (b + np.roll(b, -1, axis=0))
    total = 0.0
    for i0 in range(0, len(a), int(chunk)):
        r = ma[i0:i0+chunk, None, :] - mb[None, :, :]
        den = np.sum(r*r, axis=2) ** 1.5
        cr = np.cross(da[i0:i0+chunk, None, :], db[None, :, :])
        good = den > 0.0
        term = np.zeros_like(den)
        term[good] = np.einsum("ijk,ijk->ij", cr, r)[good] / den[good]
        total += float(term.sum())
    return total / (4.0 * math.pi)


def audit_record(record: dict[str, Any], *, samples: int | None = None,
                 scale_mode: str = "native", core_radius: float = R_C,
                 linking: bool = True) -> dict[str, Any]:
    n = source_sampling(record) if samples is None else int(samples)
    comps = sample_record(record, n, scale_mode=scale_mode, core_radius=core_radius)
    scale = _scale_factor(float(record["D"]), scale_mode, core_radius)
    curves = []
    for c, pts in zip(record["curves"], comps):
        calc = polyline_length(pts)
        target = float(c["L"]) * scale
        curves.append({
            "index": int(c["index"]), "samples": n,
            "target_length": target, "sampled_length": calc,
            "relative_length_error": (calc / target - 1.0) if target else 0.0,
            "coeff_count": len(c["coeffs"]),
            "max_harmonic": max(i for i, _, _ in c["coeffs"]),
        })
    pairs = []
    if linking and len(comps) > 1:
        for i in range(len(comps)):
            for j in range(i+1, len(comps)):
                lk = gauss_linking_number(comps[i], comps[j])
                pairs.append({"i": i+1, "j": j+1, "gauss_linking": lk, "nearest_integer": int(round(lk))})
    return {
        "kind": record["kind"], "id": record["id"], "conway": record.get("conway", ""),
        "D_native": float(record["D"]), "scale_mode": scale_mode,
        "scale_factor_m_per_native": scale if scale_mode != "native" else None,
        "source_sampling": source_sampling(record), "samples_used": n,
        "component_count": len(comps), "curves": curves, "linking_pairs": pairs,
    }


def _sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def catalog_summary(knot_path: str | Path = DEFAULT_IDEAL_KNOTS,
                    link_path: str | Path = DEFAULT_IDEAL_LINKS) -> dict[str, Any]:
    knot_ids = list_knot_ids(knot_path)
    link_ids = list_link_ids(link_path)
    return {
        "knot_database": str(Path(knot_path)), "link_database": str(Path(link_path)),
        "knot_database_sha256": _sha256_file(knot_path), "link_database_sha256": _sha256_file(link_path),
        "knot_count": len(knot_ids), "link_count": len(link_ids),
        "knot_first": knot_ids[0] if knot_ids else None, "knot_last": knot_ids[-1] if knot_ids else None,
        "link_first": link_ids[0] if link_ids else None, "link_last": link_ids[-1] if link_ids else None,
    }
