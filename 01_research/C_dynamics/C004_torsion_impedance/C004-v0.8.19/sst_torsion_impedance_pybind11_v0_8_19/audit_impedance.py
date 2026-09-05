#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np

try:
    from sst_torsion_impedance_build import import_module as _import_sti
    sti = _import_sti(auto_build=True)
    HAVE_EXTENSION = True
except Exception:
    # Keep the audit script usable on machines without pybind11 by falling back
    # to the pure-NumPy implementation below. The test script remains stricter.
    sti = None
    HAVE_EXTENSION = False

C = 299792458.0
VCHAR = 1.09384563e6
R_C = 1.40897017e-15
RHO_F = 7.0e-7
RHO_CORE = 3.8934358266918687e18
M_E = 9.1093837015e-31
ELECTRON_REST_ENERGY_J = M_E * C * C

Coeff = Tuple[int, np.ndarray, np.ndarray]


def extract_ab_block(text: str, ab_id: str) -> str:
    m = re.search(rf'<AB\s+Id="{re.escape(ab_id)}"[^>]*>.*?</AB>', text, re.S)
    if not m:
        raise KeyError(f"AB id not found: {ab_id}")
    return m.group(0)


def parse_ab_coefficients(block: str) -> Tuple[float, float, List[Coeff]]:
    header = block.split(">", 1)[0]
    L = float(re.search(r'\bL="([^"]+)"', header).group(1))
    Dm = re.search(r'\bD="([^"]+)"', header)
    D = float(Dm.group(1)) if Dm else 1.0
    coeffs: List[Coeff] = []
    for tag in re.findall(r'<Coeff\b[^>]*/>', block):
        idx = int(re.search(r'\bI="\s*([0-9]+)"', tag).group(1))
        A = np.fromstring(re.search(r'\bA="([^"]+)"', tag).group(1), sep=",", dtype=float)
        B = np.fromstring(re.search(r'\bB="([^"]+)"', tag).group(1), sep=",", dtype=float)
        if A.shape != (3,) or B.shape != (3,):
            raise ValueError(f"Bad coefficient tag: {tag}")
        coeffs.append((idx, A, B))
    return L, D, coeffs


def evaluate_fourier(coeffs: Iterable[Coeff], n: int) -> np.ndarray:
    s = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    P = np.zeros((n, 3), dtype=float)
    for idx, A, B in coeffs:
        P += np.cos(idx * s)[:, None] * A + np.sin(idx * s)[:, None] * B
    return P


def analytic_trefoil(n: int) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    R, r = 2.0, 0.75
    return np.column_stack(((R + r*np.cos(3*t))*np.cos(2*t),
                            (R + r*np.cos(3*t))*np.sin(2*t),
                            r*np.sin(3*t)))


def analytic_figure_eight(n: int) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return np.column_stack(((2.0 + np.cos(2*t))*np.cos(3*t),
                            (2.0 + np.cos(2*t))*np.sin(3*t),
                            np.sin(4*t)))


def audit_numpy(points: np.ndarray, density_kg_m3: float, rest_energy_j: float = ELECTRON_REST_ENERGY_J,
                c_T_m_s: float = C, length_scale_m: float = R_C, core_radius_m: float = R_C,
                impedance_scale: float = 1.0) -> Dict[str, object]:
    P = np.asarray(points, dtype=float)
    if P.ndim != 2 or P.shape[1] != 3 or P.shape[0] < 3:
        raise ValueError("points must have shape (N,3), N>=3")
    A = math.pi * core_radius_m ** 2
    M = np.zeros((3, 3), dtype=float)
    L = 0.0
    I = np.eye(3)
    for i in range(P.shape[0]):
        d = (P[(i + 1) % P.shape[0]] - P[i]) * length_scale_m
        ds = float(np.linalg.norm(d))
        if ds <= 0.0:
            continue
        t = d / ds
        M += impedance_scale * density_kg_m3 * A * ds * (I - np.outer(t, t))
        L += ds
    eig = np.linalg.eigvalsh(M)
    lam = float(np.trace(M) / 3.0)
    target = float(2.0 * rest_energy_j / (c_T_m_s ** 2))
    chi = float(lam / target) if target > 0 else math.inf
    return {
        "backend": "numpy-reference",
        "length_m": L,
        "length_over_r_c": float(L / R_C),
        "density_kg_m3": density_kg_m3,
        "lambda_iso_kg": lam,
        "target_lambda_iso_kg": target,
        "chi_T": chi,
        "eigenvalues_kg": eig.tolist(),
        "eigenvalues_over_lambda_iso": (eig / lam).tolist() if lam else [math.nan] * 3,
        "isotropy_residual": float((eig[-1] - eig[0]) / lam) if lam else math.nan,
        "required_impedance_scale_for_chi_one": float(impedance_scale / chi) if chi > 0 else math.inf,
        "required_density_for_chi_one_kg_m3": float(density_kg_m3 / chi) if chi > 0 else math.inf,
    }


def audit_points(points: np.ndarray, density_kg_m3: float) -> Dict[str, object]:
    if HAVE_EXTENSION:
        opt = sti.Options()
        opt.density_kg_m3 = density_kg_m3
        out = sti.audit_points(np.asarray(points, dtype=np.float64), opt)
        out = dict(out)
        out["backend"] = "pybind11-extension"
        out["density_kg_m3"] = density_kg_m3
        return out
    return audit_numpy(points, density_kg_m3)


def run_cases(points_by_case: Dict[str, Tuple[str, np.ndarray, Dict[str, float]]]) -> Dict[str, object]:
    out: Dict[str, object] = {"extension_loaded": HAVE_EXTENSION, "cases": {}}
    for ab_id, (name, P, meta) in points_by_case.items():
        out["cases"][ab_id] = {
            "name": name,
            **meta,
            "rho_f": audit_points(P, RHO_F),
            "rho_core": audit_points(P, RHO_CORE),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ideal", type=Path, default=None, help="Path to SSTcore examples/ideal.txt")
    ap.add_argument("--analytic", action="store_true", help="Use analytic trefoil/figure-eight instead of ideal.txt")
    ap.add_argument("--n", type=int, default=4096, help="Samples per closed curve")
    ap.add_argument("--ids", default="3:1:1,4:1:1", help="Comma-separated AB ids when using ideal.txt")
    ap.add_argument("--json", type=Path, default=None, help="Optional output JSON path")
    args = ap.parse_args()

    if args.n < 8:
        raise ValueError("--n must be >= 8")

    if args.analytic or args.ideal is None:
        cases = {
            "analytic:3_1": ("analytic_trefoil", analytic_trefoil(args.n), {"samples": args.n}),
            "analytic:4_1": ("analytic_figure_eight", analytic_figure_eight(args.n), {"samples": args.n}),
        }
        out = run_cases(cases)
    else:
        text = args.ideal.read_text(encoding="utf-8", errors="replace")
        ids = [s.strip() for s in args.ids.split(",") if s.strip()]
        cases = {}
        for ab_id in ids:
            L, D, coeffs = parse_ab_coefficients(extract_ab_block(text, ab_id))
            cases[ab_id] = ("ideal_AB_" + ab_id, evaluate_fourier(coeffs, args.n),
                            {"samples": args.n, "listed_L": L, "listed_D": D})
        out = run_cases(cases)
        out["ideal_txt"] = str(args.ideal)

    s = json.dumps(out, indent=2)
    print(s)
    if args.json:
        args.json.write_text(s + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
