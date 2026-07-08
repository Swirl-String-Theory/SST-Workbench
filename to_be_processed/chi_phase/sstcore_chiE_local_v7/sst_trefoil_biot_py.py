from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

_FLOAT = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
PI = math.pi


@dataclass(frozen=True)
class SSTConstants:
    v_swirl: float = 1.09384563e6          # m s^-1
    r_c: float = 1.40897017e-15            # m
    rho_f: float = 7.0e-7                  # kg m^-3
    c: float = 2.99792458e8                # m s^-1

    @property
    def gamma_0(self) -> float:
        # Canon circulation closure: Gamma_0 = 2 pi r_c v_swirl.
        return 2.0 * PI * self.r_c * self.v_swirl

    @property
    def natural_length(self) -> float:
        # L0 = Gamma_0 / v_swirl = 2 pi r_c.
        return self.gamma_0 / self.v_swirl

    @property
    def alpha_sst_inverse(self) -> float:
        # Canon comparison scale alpha_SST = 2 v_swirl / c.
        return self.c / (2.0 * self.v_swirl)


DEFAULT_CONSTANTS = SSTConstants()


@dataclass(frozen=True)
class IdealKnot:
    knot_id: str
    conway: Optional[str]
    length_L: Optional[float]
    diameter_D: Optional[float]
    A: np.ndarray
    B: np.ndarray
    I: np.ndarray


def _parse_vec(text: str) -> Tuple[float, float, float]:
    vals = [float(v) for v in re.findall(_FLOAT, text)]
    if len(vals) != 3:
        raise ValueError(f"Expected 3-vector, got {text!r}")
    return vals[0], vals[1], vals[2]


def _attr(block_header: str, name: str) -> Optional[str]:
    m = re.search(rf'{name}="([^"]*)"', block_header)
    return m.group(1).strip() if m else None


def load_ideal_knot(path: str | Path, knot_id: str = "3:1:1") -> IdealKnot:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    m = re.search(rf'(<AB\s+[^>]*Id="{re.escape(knot_id)}"[^>]*>)(.*?)(</AB>)', text, flags=re.S)
    if not m:
        raise KeyError(f"Knot Id={knot_id!r} not found in {path}")
    header, body = m.group(1), m.group(2)
    coeffs: List[Tuple[int, Tuple[float, float, float], Tuple[float, float, float]]] = []
    for cm in re.finditer(r'<Coeff\s+([^>]*)/>', body):
        attrs = cm.group(1)
        i_s = _attr(attrs, "I")
        a_s = _attr(attrs, "A")
        b_s = _attr(attrs, "B")
        if i_s is None or a_s is None or b_s is None:
            continue
        coeffs.append((int(i_s), _parse_vec(a_s), _parse_vec(b_s)))
    if not coeffs:
        raise ValueError(f"No <Coeff> entries found for Id={knot_id}")
    coeffs.sort(key=lambda x: x[0])
    return IdealKnot(
        knot_id=knot_id,
        conway=_attr(header, "Conway"),
        length_L=float(_attr(header, "L")) if _attr(header, "L") is not None else None,
        diameter_D=float(_attr(header, "D")) if _attr(header, "D") is not None else None,
        A=np.array([c[1] for c in coeffs], dtype=np.float64),
        B=np.array([c[2] for c in coeffs], dtype=np.float64),
        I=np.array([c[0] for c in coeffs], dtype=np.int32),
    )


def sample_fourier_knot(knot: IdealKnot, n: int = 384, endpoint: bool = False) -> np.ndarray:
    if n < 8:
        raise ValueError("n must be >= 8")
    t = np.linspace(0.0, 2.0 * PI, n, endpoint=endpoint)
    pts = np.zeros((t.size, 3), dtype=np.float64)
    for i, a, b in zip(knot.I, knot.A, knot.B):
        pts += np.cos(i * t)[:, None] * a[None, :]
        pts += np.sin(i * t)[:, None] * b[None, :]
    return pts


def closed_polyline_length(points: np.ndarray, cpp_mod: Any = None) -> float:
    p = np.asarray(points, dtype=np.float64)
    if cpp_mod is not None:
        return float(cpp_mod.polyline_length(p))
    return float(np.linalg.norm(np.roll(p, -1, axis=0) - p, axis=1).sum())


def min_nonadjacent_vertex_distance(points: np.ndarray, skip: int = 2, cpp_mod: Any = None) -> float:
    p = np.asarray(points, dtype=np.float64)
    if cpp_mod is not None:
        return float(cpp_mod.min_nonadjacent_vertex_distance(p, int(skip)))
    n = len(p)
    best = np.inf
    for i in range(n):
        for j in range(i + 1, n):
            sep = min(j - i, n - (j - i))
            if sep <= skip:
                continue
            d = float(np.linalg.norm(p[j] - p[i]))
            if d < best:
                best = d
    return float(best)


def _segment_geometry(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = np.asarray(points, dtype=np.float64)
    q = np.roll(p, -1, axis=0)
    dl = q - p
    ds = np.linalg.norm(dl, axis=1)
    if np.any(ds <= 0.0):
        raise ValueError("Degenerate segment in closed polyline")
    return 0.5 * (p + q), dl / ds[:, None], ds


def bs_energy_dimensionless(points: np.ndarray, a_dim: float, mode: str = "regularized", cpp_mod: Any = None) -> float:
    p = np.asarray(points, dtype=np.float64)
    if cpp_mod is not None:
        if mode == "cutoff":
            return float(cpp_mod.bs_cutoff_energy(p, float(a_dim)))
        return float(cpp_mod.bs_regularized_energy(p, float(a_dim)))
    mid, tang, ds = _segment_geometry(p)
    r = mid[:, None, :] - mid[None, :, :]
    dist2 = np.einsum("ijk,ijk->ij", r, r)
    dot = tang @ tang.T
    weight = ds[:, None] * ds[None, :]
    mask = ~np.eye(len(p), dtype=bool)
    if mode == "cutoff":
        dist = np.sqrt(dist2)
        mask &= dist > a_dim
        kernel = np.zeros_like(dist)
        kernel[mask] = dot[mask] * weight[mask] / dist[mask]
    else:
        denom = np.sqrt(dist2 + a_dim * a_dim)
        kernel = np.zeros_like(denom)
        kernel[mask] = dot[mask] * weight[mask] / denom[mask]
    return float(kernel.sum() / (8.0 * PI))


def velocity_grid(points: np.ndarray, eval_points: np.ndarray, gamma: float = 1.0, a_dim: float = 1e-3, cpp_mod: Any = None) -> np.ndarray:
    p = np.asarray(points, dtype=np.float64)
    x = np.asarray(eval_points, dtype=np.float64)
    if cpp_mod is not None:
        return np.asarray(cpp_mod.velocity_grid(p, x, float(gamma), float(a_dim)))
    mid, tang, ds = _segment_geometry(p)
    out = np.zeros_like(x, dtype=np.float64)
    coeff = gamma / (4.0 * PI)
    for k, r0 in enumerate(x):
        rr = r0[None, :] - mid
        denom = (np.einsum("ij,ij->i", rr, rr) + a_dim * a_dim) ** 1.5
        out[k] = coeff * (np.cross(tang, rr) * (ds / denom)[:, None]).sum(axis=0)
    return out


def total_energy_joule(
    points_dim: np.ndarray,
    a_over_rc: float,
    constants: SSTConstants = DEFAULT_CONSTANTS,
    mode: str = "regularized",
    pressure_penalty_lambda: float = 0.0,
    cpp_mod: Any = None,
) -> Dict[str, float]:
    L0 = constants.natural_length
    gamma0 = constants.gamma_0
    a_phys = a_over_rc * constants.r_c
    a_dim = a_phys / L0
    L_dim = closed_polyline_length(points_dim, cpp_mod=cpp_mod)
    L_phys = L_dim * L0
    e_bs_dim = bs_energy_dimensionless(points_dim, a_dim, mode=mode, cpp_mod=cpp_mod)
    e_bs = constants.rho_f * gamma0 * gamma0 * L0 * e_bs_dim
    e_core = 0.5 * PI * constants.rho_f * constants.v_swirl**2 * a_phys * a_phys * L_phys
    e_penalty = pressure_penalty_lambda * constants.rho_f * gamma0 * gamma0 * L_phys * (a_over_rc - 1.0) ** 2
    return {
        "a_over_rc": float(a_over_rc),
        "a_phys_m": float(a_phys),
        "a_dim": float(a_dim),
        "L_dim": float(L_dim),
        "L_phys_m": float(L_phys),
        "E_bs_dimless": float(e_bs_dim),
        "E_bs_J": float(e_bs),
        "E_core_J": float(e_core),
        "E_penalty_J": float(e_penalty),
        "E_total_J": float(e_bs + e_core + e_penalty),
    }


def golden_section_min(f, lo: float, hi: float, iters: int = 32) -> Tuple[float, float]:
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c = hi - gr * (hi - lo)
    d = lo + gr * (hi - lo)
    fc = f(c)
    fd = f(d)
    for _ in range(iters):
        if fc < fd:
            hi, d, fd = d, c, fc
            c = hi - gr * (hi - lo)
            fc = f(c)
        else:
            lo, c, fc = c, d, fd
            d = lo + gr * (hi - lo)
            fd = f(d)
    x = 0.5 * (lo + hi)
    return x, f(x)


def scan_closure(
    ideal_path: str | Path,
    knot_id: str = "3:1:1",
    n: int = 384,
    a_min: float = 0.20,
    a_max: float = 3.00,
    samples: int = 60,
    mode: str = "regularized",
    pressure_penalty_lambda: float = 0.0,
    cpp_mod: Any = None,
) -> Tuple[Dict[str, Any], List[Dict[str, float]], np.ndarray]:
    constants = DEFAULT_CONSTANTS
    knot = load_ideal_knot(ideal_path, knot_id=knot_id)
    pts = sample_fourier_knot(knot, n=n, endpoint=False)
    closure_pair = sample_fourier_knot(knot, n=8, endpoint=True)
    grid = np.geomspace(a_min, a_max, samples)
    rows = [total_energy_joule(pts, float(x), constants, mode, pressure_penalty_lambda, cpp_mod) for x in grid]
    best_i = int(np.argmin([r["E_total_J"] for r in rows]))
    lo_i = max(0, best_i - 1)
    hi_i = min(len(grid) - 1, best_i + 1)
    lo = math.log(grid[lo_i])
    hi = math.log(grid[hi_i])
    if hi <= lo:
        lo, hi = math.log(a_min), math.log(a_max)

    def f(log_x: float) -> float:
        return total_energy_joule(pts, math.exp(log_x), constants, mode, pressure_penalty_lambda, cpp_mod)["E_total_J"]

    log_star, _ = golden_section_min(f, lo, hi)
    best = total_energy_joule(pts, math.exp(log_star), constants, mode, pressure_penalty_lambda, cpp_mod)
    skip = max(2, n // 20)
    probe = np.array([[0.0, 0.0, 0.0], [0.25, 0.0, 0.0], [0.0, 0.25, 0.0]], dtype=np.float64)
    v_probe = velocity_grid(pts, probe, gamma=1.0, a_dim=best["a_dim"], cpp_mod=cpp_mod)
    summary: Dict[str, Any] = {
        "knot_id": knot.knot_id,
        "conway": knot.conway,
        "declared_L": knot.length_L,
        "declared_D": knot.diameter_D,
        "sample_N": int(n),
        "polyline_L_dim": closed_polyline_length(pts, cpp_mod=cpp_mod),
        "min_nonlocal_vertex_distance_dim": min_nonadjacent_vertex_distance(pts, skip=skip, cpp_mod=cpp_mod),
        "min_nonlocal_skip_vertices": int(skip),
        "fourier_closure_error_dim": float(np.linalg.norm(closure_pair[0] - closure_pair[-1])),
        "constants": asdict(constants),
        "gamma0_m2_s": constants.gamma_0,
        "natural_length_m": constants.natural_length,
        "alpha_sst_inverse": constants.alpha_sst_inverse,
        "mode": mode,
        "pressure_penalty_lambda": float(pressure_penalty_lambda),
        "best": best,
        "chi_eff": best["a_phys_m"] * constants.v_swirl / constants.gamma_0,
        "chi_req_1_over_2pi": 1.0 / (2.0 * PI),
        "velocity_probe_points_dim": probe.tolist(),
        "velocity_probe_gamma1": v_probe.tolist(),
        "status": "RESEARCH-TRACK numerical closure scan; not a proof of ideal ropelength minimality.",
    }
    return summary, rows, pts


def write_csv(path: str | Path, rows: List[Dict[str, float]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_xyz(path: str | Path, points: np.ndarray) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(p, points, fmt="%.17g", header="x y z")
