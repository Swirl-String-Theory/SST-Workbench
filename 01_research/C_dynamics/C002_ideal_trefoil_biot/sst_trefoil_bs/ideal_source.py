#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ideal_source.py
===============
Unified resolver for the Brian Gilbert ideal-knot database
(ideal.txt, <AB> XML format, 263 knots 3-10 crossings).

Resolution order (first hit wins):
  1. SSTcore bundled   -> ssc.get_ideal_txt_path()
  2. env override      -> $SST_IDEAL_TXT
  3. local candidates  -> ./ideal.txt, ./resources/ideal.txt, module-dir, cache-dir
  4. GitHub raw        -> SSTcore/master/resources/ideal.txt  (cached)
  5. katlas.org gz     -> katlas.org/images/d/d2/Ideal.txt.gz (cached)

Downloads go to $SST_CACHE_DIR or ~/.cache/sst — never CWD.

Format recap
------------
  <AB Id="3:1:1" Conway="3" L="16.371637" D=" 1.000000">
    <Coeff I="1"  A=" ax, ay, az" B=" bx, by, bz" />
    ...
  </AB>

  r(t) = sum_k [ A_k cos(k t) + B_k sin(k t) ]   t in [0, 2pi]
  L    = arc length  (in units where D = tube diameter)
  D    = tube diameter  (always 1.0 in the database)
  tube radius a = D/2
  ropelength   = L / a = 2L   (since D=1 → a=0.5)
"""

from __future__ import annotations

import gzip
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

# Workbench root (…/SST-Workbench) for shared Gilbert usability helpers.
_WORKBENCH = Path(__file__).resolve().parents[2]
if str(_WORKBENCH) not in sys.path:
    sys.path.insert(0, str(_WORKBENCH))

try:
    from sst_gilbert_usability import (
        DEFAULT_MIN_C_CONT,
        CurvatureOnlyIdealError,
        usability_from_coeffs,
    )
except ImportError:  # pragma: no cover
    DEFAULT_MIN_C_CONT = 0.05
    CurvatureOnlyIdealError = ValueError  # type: ignore[misc, assignment]
    usability_from_coeffs = None  # type: ignore[assignment]

# ── URL constants ──────────────────────────────────────────────────────────
_GITHUB_RAW = (
    "https://raw.githubusercontent.com/"
    "Swirl-String-Theory/SSTcore/master/resources/ideal.txt"
)
_KATLAS_GZ = "https://katlas.org/images/d/d2/Ideal.txt.gz"
_CACHE_DIR = Path(os.environ.get("SST_CACHE_DIR", Path.home() / ".cache" / "sst"))


# ── Resolver ───────────────────────────────────────────────────────────────

def resolve_ideal_txt() -> Path:
    """Return a Path to a readable ideal.txt, fetching/caching if needed."""
    import urllib.request

    # 1. SSTcore bundled
    try:
        import SSTcore as ssc
        p = Path(ssc.get_ideal_txt_path())
        if p.exists() and p.stat().st_size > 100_000:
            return p
    except Exception:
        pass

    # 2. env override
    env = os.environ.get("SST_IDEAL_TXT")
    if env:
        p = Path(env)
        if p.exists():
            return p

    # 3. local candidates
    script_dir = Path(__file__).resolve().parent
    candidates = ["ideal.txt", "resources/ideal.txt", "exports/ideal.txt"]
    search_roots = [Path.cwd(), script_dir, _CACHE_DIR]
    for root in search_roots:
        for rel in candidates:
            p = root / rel
            if p.exists() and p.stat().st_size > 100_000:
                return p

    # 4. GitHub raw (cached)
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = _CACHE_DIR / "ideal.txt"

    if cached.exists() and cached.stat().st_size > 100_000:
        return cached

    print(f"[ideal_source] Downloading ideal.txt from GitHub … ", end="", flush=True)
    try:
        urllib.request.urlretrieve(_GITHUB_RAW, cached)
        if cached.exists() and cached.stat().st_size > 100_000:
            print("OK")
            return cached
        else:
            print("truncated, trying katlas")
    except Exception as e:
        print(f"failed ({e}), trying katlas")

    # 5. katlas.org gz (cached)
    gz_path = _CACHE_DIR / "ideal.txt.gz"
    print(f"[ideal_source] Downloading ideal.txt.gz from katlas.org … ", end="", flush=True)
    try:
        urllib.request.urlretrieve(_KATLAS_GZ, gz_path)
        with gzip.open(gz_path, "rb") as fin, open(cached, "wb") as fout:
            fout.write(fin.read())
        if cached.exists() and cached.stat().st_size > 100_000:
            print("OK")
            return cached
        else:
            print("truncated")
    except Exception as e:
        print(f"failed ({e})")

    raise FileNotFoundError(
        "Could not resolve ideal.txt.\n"
        "  • Place ideal.txt in the current directory, OR\n"
        "  • Set $SST_IDEAL_TXT to the file path, OR\n"
        "  • Set $SST_CACHE_DIR to a writable directory with network access."
    )


# ── Parser ─────────────────────────────────────────────────────────────────

def _parse_float3(s: str) -> np.ndarray:
    """Parse 'x, y, z' triplet → numpy array shape (3,)."""
    return np.array([float(v.strip()) for v in s.split(",")])


def load_knot(
    knot_id: str = "3:1:1",
    ideal_path: Optional[Path] = None,
    *,
    require_contact: bool = True,
    min_c_cont: float = DEFAULT_MIN_C_CONT,
    usability_samples: int = 384,
) -> Tuple[float, float, Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """
    Load one knot from ideal.txt by its AB Id (e.g. '3:1:1').

    By default, rejects curvature-only Fourier artifacts with C_cont <= min_c_cont.
    Pass require_contact=False only for diagnostics.

    Returns
    -------
    L          : arc length (in ideal.txt units, D=1)
    D          : tube diameter (=1.0 always in this database)
    cos_coeffs : dict  k -> np.array([ax, ay, az])   (A_k, cosine mode k)
    sin_coeffs : dict  k -> np.array([bx, by, bz])   (B_k, sine   mode k)

    Curve:  r(t) = sum_k [ A_k cos(k t) + B_k sin(k t) ],  t in [0, 2pi]
    """
    path = ideal_path or resolve_ideal_txt()
    text = Path(path).read_text(encoding="ascii", errors="replace")

    # Extract the <AB Id="3:1:1" ...>...</AB> block
    pattern = rf'<AB\s+Id="{re.escape(knot_id)}"[^>]*>.*?</AB>'
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        raise ValueError(f"Knot Id='{knot_id}' not found in {path}")

    block = m.group(0)

    # Parse as XML (the block is valid XML)
    root = ET.fromstring(block)
    L = float(root.get("L", "0"))
    D = float(root.get("D", "1").strip())

    cos_coeffs: Dict[int, np.ndarray] = {}
    sin_coeffs: Dict[int, np.ndarray] = {}

    for coeff in root.findall("Coeff"):
        i = int(coeff.get("I").strip())
        a_str = coeff.get("A", "0,0,0").strip()
        b_str = coeff.get("B", "0,0,0").strip()
        cos_coeffs[i] = _parse_float3(a_str)
        sin_coeffs[i] = _parse_float3(b_str)

    if require_contact:
        if usability_from_coeffs is None:
            raise ImportError(
                "sst_gilbert_usability is required for the C_cont gate; "
                "install/work from SST-Workbench or pass require_contact=False"
            )
        modes = sorted(set(cos_coeffs) | set(sin_coeffs))
        coeff_list = []
        for k in modes:
            a = cos_coeffs.get(k, np.zeros(3))
            b = sin_coeffs.get(k, np.zeros(3))
            coeff_list.append((k, tuple(map(float, a)), tuple(map(float, b))))
        _pts, report = usability_from_coeffs(
            coeff_list, D=D, samples=usability_samples, min_c_cont=min_c_cont
        )
        if not report["usable"]:
            raise CurvatureOnlyIdealError(
                f"Gilbert {knot_id} fails C_cont gate: "
                f"C_cont={report['C_cont']:.6g} <= {min_c_cont} "
                f"(kappa_hat_max={report['kappa_hat_max']:.6g}). "
                f"Pass require_contact=False only for diagnostics."
            )

    return L, D, cos_coeffs, sin_coeffs


# ── Curve evaluator ────────────────────────────────────────────────────────

def eval_curve(
    cos_coeffs: Dict[int, np.ndarray],
    sin_coeffs: Dict[int, np.ndarray],
    N: int = 600,
) -> np.ndarray:
    """
    Evaluate the Fourier series at N equally-spaced t in [0, 2pi).

    Returns
    -------
    pts : np.ndarray shape (N, 3)
    """
    t = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    pts = np.zeros((N, 3))
    for k, a in cos_coeffs.items():
        pts += np.outer(np.cos(k * t), a)
    for k, b in sin_coeffs.items():
        pts += np.outer(np.sin(k * t), b)
    return pts


def arc_length(pts: np.ndarray) -> float:
    """Numerical arc length of a closed polygon (N,3)."""
    dp = np.roll(pts, -1, axis=0) - pts
    return float(np.sum(np.linalg.norm(dp, axis=1)))
