#!/usr/bin/env python3
"""
sst_ffs_00_reproduce_g1.py

Reproduce / fit a one-particle or phase-correlation curve G^(1)(x) against the
ideal fractional-Fermi-sea / SST-Rosetta correlator

    G_l^(1)(x) ~= A sinc(q_edge*x/pi) exp(-x/xi) + B,
    q_edge = ell*q0, q0 = pi*n_line.

Use this for the experimental/Zenodo g1 data once the raw CSV is available.
It also has a deterministic --demo mode so the full pipeline is testable.

Examples
--------
Demo data:
    python sst_ffs_00_reproduce_g1.py --demo --ell-demo 2 --outdir results_00

CSV data with x in micrometers:
    python sst_ffs_00_reproduce_g1.py --input g1.csv --x-unit um --outdir results_00

Expected CSV columns:
    x,g1
or named variants such as distance_um, corr, G1. If no names match, the first
numeric column is x and the second is g1.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np

FALLBACK_V_SWIRL = 1.09384563e6  # m s^-1


def load_v_swirl() -> tuple[float, str]:
    try:
        import SSTcore as sst  # type: ignore
        for name in ("v_swirl", "V_SWIRL", "C_e", "Ce"):
            if hasattr(sst, name):
                val = getattr(sst, name)
                if hasattr(val, "value"):
                    val = val.value
                return float(val), "SSTcore"
    except Exception:
        pass
    return FALLBACK_V_SWIRL, "fallback canonical constants"


def unit_factor(unit: str) -> float:
    u = unit.lower()
    if u in ("m", "meter", "meters"):
        return 1.0
    if u in ("um", "µm", "micrometer", "micrometers"):
        return 1.0e-6
    if u in ("nm", "nanometer", "nanometers"):
        return 1.0e-9
    if u in ("mm", "millimeter", "millimeters"):
        return 1.0e-3
    raise ValueError(f"Unknown x unit: {unit}")


def load_xy_csv(path: Path, x_unit: str) -> tuple[np.ndarray, np.ndarray]:
    factor = unit_factor(x_unit)

    try:
        data = np.genfromtxt(path, delimiter=",", names=True, dtype=float, comments="#")
        if data.dtype.names:
            names = list(data.dtype.names)
            lower = {n.lower(): n for n in names}

            x_candidates = [n for n in names if any(k in n.lower() for k in ("x", "dist", "distance", "s"))]
            y_candidates = [n for n in names if any(k in n.lower() for k in ("g1", "corr", "correlation", "value", "y"))]
            x_name = lower.get("x") or (x_candidates[0] if x_candidates else None)
            y_name = lower.get("g1") or lower.get("g") or (y_candidates[0] if y_candidates else None)
            if x_name and y_name and x_name != y_name:
                x = np.asarray(data[x_name], dtype=float) * factor
                y = np.asarray(data[y_name], dtype=float)
                mask = np.isfinite(x) & np.isfinite(y)
                if np.count_nonzero(mask) >= 5:
                    return x[mask], y[mask]
    except Exception:
        pass

    for delim in (",", None):
        try:
            arr = np.loadtxt(path, delimiter=delim, comments="#")
            arr = np.asarray(arr, dtype=float)
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)
            if arr.shape[1] >= 2:
                x = arr[:, 0] * factor
                y = arr[:, 1]
                mask = np.isfinite(x) & np.isfinite(y)
                if np.count_nonzero(mask) >= 5:
                    return x[mask], y[mask]
        except Exception:
            continue

    raise ValueError(f"Could not read at least two numeric columns from {path}")


def model_g1(x: np.ndarray, A: float, q_edge: float, xi: float, B: float) -> np.ndarray:
    envelope = np.exp(-np.maximum(x, 0.0) / xi) if np.isfinite(xi) and xi > 0 else 1.0
    return A * np.sinc(q_edge * x / math.pi) * envelope + B


@dataclass
class FitResult:
    constants_source: str
    v_swirl_m_s: float
    n_points: int
    n_line_m_inv: float
    q0_m_inv: float
    A: float
    q_edge_m_inv: float
    xi_m: float
    B: float
    ell_fit: float
    x1_m: float
    f_edge_Hz: float
    rmse: float
    r2: float
    fit_method: str


def fit_with_scipy(x: np.ndarray, y: np.ndarray, q0: float) -> Optional[tuple[float, float, float, float, str]]:
    try:
        from scipy.optimize import curve_fit  # type: ignore
    except Exception:
        return None

    xmax = float(np.max(x) - np.min(x))
    if xmax <= 0:
        return None

    A0 = float(np.max(y) - np.min(y)) or 1.0
    B0 = float(np.mean(y[-max(3, len(y)//10):]))
    q0_guess = 2.0 * q0
    xi0 = max(xmax, 1e-30)
    p0 = [A0, q0_guess, xi0, B0]
    lower = [-np.inf, 1e-12, xmax / 100.0, -np.inf]
    upper = [np.inf, 100.0 * q0, 100.0 * xmax, np.inf]

    try:
        popt, _pcov = curve_fit(lambda xx, A, qe, xi, B: model_g1(xx, A, qe, xi, B), x, y, p0=p0, bounds=(lower, upper), maxfev=20000)
        return float(popt[0]), float(popt[1]), float(popt[2]), float(popt[3]), "scipy.curve_fit"
    except Exception:
        return None


def fit_grid_linear(x: np.ndarray, y: np.ndarray, q0: float, q_min_mult: float = 0.25, q_max_mult: float = 16.0):
    """Fallback fit: grid q_edge and xi; solve A,B by linear least squares."""
    xmax = float(np.max(x) - np.min(x))
    if xmax <= 0:
        raise ValueError("x range must be positive")

    q_grid = np.linspace(q_min_mult * q0, q_max_mult * q0, 800)
    xi_grid = np.geomspace(max(xmax / 20.0, 1e-30), max(20.0 * xmax, 1e-29), 80)
    best = None

    for qe in q_grid:
        sinc = np.sinc(qe * x / math.pi)
        for xi in xi_grid:
            basis = sinc * np.exp(-np.maximum(x, 0.0) / xi)
            M = np.column_stack([basis, np.ones_like(x)])
            coeff, *_ = np.linalg.lstsq(M, y, rcond=None)
            yhat = M @ coeff
            sse = float(np.sum((y - yhat) ** 2))
            if best is None or sse < best[0]:
                best = (sse, float(coeff[0]), float(qe), float(xi), float(coeff[1]))

    assert best is not None
    _sse, A, qe, xi, B = best
    return A, qe, xi, B, "grid_linear_lstsq"


def compute_fit(x: np.ndarray, y: np.ndarray, n_line_m_inv: float, v_swirl: float, source: str) -> tuple[FitResult, np.ndarray]:
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    q0 = math.pi * n_line_m_inv

    fit = fit_with_scipy(x, y, q0)
    if fit is None:
        fit = fit_grid_linear(x, y, q0)
    A, q_edge, xi, B, method = fit
    yhat = model_g1(x, A, q_edge, xi, B)

    residual = y - yhat
    rmse = float(np.sqrt(np.mean(residual**2)))
    sst = float(np.sum((y - np.mean(y))**2))
    sse = float(np.sum(residual**2))
    r2 = 1.0 - sse / sst if sst > 0 else float("nan")

    result = FitResult(
        constants_source=source,
        v_swirl_m_s=float(v_swirl),
        n_points=int(len(x)),
        n_line_m_inv=float(n_line_m_inv),
        q0_m_inv=float(q0),
        A=float(A),
        q_edge_m_inv=float(q_edge),
        xi_m=float(xi),
        B=float(B),
        ell_fit=float(q_edge / q0),
        x1_m=float(math.pi / q_edge),
        f_edge_Hz=float(v_swirl * q_edge / (2.0 * math.pi)),
        rmse=rmse,
        r2=float(r2),
        fit_method=method,
    )
    return result, yhat


def make_demo(ell: float, n_line_um_inv: float, n: int = 240, noise: float = 0.015, seed: int = 42):
    rng = np.random.default_rng(seed)
    x = np.linspace(0.0, 4.0e-6, n)
    q0 = math.pi * n_line_um_inv * 1e6
    q_edge = ell * q0
    y_clean = model_g1(x, A=0.92, q_edge=q_edge, xi=3.0e-6, B=0.03)
    y = y_clean + rng.normal(0.0, noise, size=n)
    return x, y


def write_fit_csv(path: Path, result: FitResult):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["quantity", "value", "unit"])
        writer.writeheader()
        for k, v in asdict(result).items():
            unit = ""
            if k.endswith("_m_s"):
                unit = "m s^-1"
            elif k.endswith("_m_inv"):
                unit = "m^-1"
            elif k.endswith("_m"):
                unit = "m"
            elif k.endswith("_Hz"):
                unit = "Hz"
            writer.writerow({"quantity": k, "value": v, "unit": unit})


def write_curve_csv(path: Path, x: np.ndarray, y: np.ndarray, yhat: np.ndarray):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["x_m", "g1", "g1_fit", "residual"])
        for xi, yi, yh in zip(x, y, yhat):
            writer.writerow([f"{xi:.16e}", f"{yi:.16e}", f"{yh:.16e}", f"{yi-yh:.16e}"])


def save_plot(path: Path, x: np.ndarray, y: np.ndarray, yhat: np.ndarray, result: FitResult):
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(x * 1e6, y, s=12, label="data")
    ax.plot(x * 1e6, yhat, linewidth=1.5, label="fit")
    ax.axhline(0.0, linewidth=0.8)
    ax.set_xlabel("x [micrometer]")
    ax.set_ylabel("G1(x)")
    ax.set_title(f"FFS G1 fit: ell={result.ell_fit:.3f}, x1={result.x1_m*1e6:.3f} um")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--x-unit", default="um", help="m, um, nm, or mm for input x column.")
    parser.add_argument("--outdir", type=Path, default=Path("sst_ffs_00_results"))
    parser.add_argument("--n-line-um-inv", type=float, default=0.5)
    parser.add_argument("--demo", action="store_true", help="Use deterministic synthetic demo data.")
    parser.add_argument("--ell-demo", type=float, default=2.0)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    v_swirl, source = load_v_swirl()

    if args.demo or args.input is None:
        x, y = make_demo(args.ell_demo, args.n_line_um_inv)
        data_source = f"synthetic_demo_ell_{args.ell_demo}"
    else:
        x, y = load_xy_csv(args.input, args.x_unit)
        data_source = str(args.input)

    result, yhat = compute_fit(x, y, args.n_line_um_inv * 1e6, v_swirl, source)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_fit_csv(args.outdir / "sst_ffs_00_fit_summary.csv", result)
    write_curve_csv(args.outdir / "sst_ffs_00_fit_curve.csv", x, y, yhat)
    if not args.no_plots:
        save_plot(args.outdir / "sst_ffs_00_g1_fit.png", x, y, yhat, result)

    print(f"data source       : {data_source}")
    print(f"constants source  : {result.constants_source}")
    print(f"fit method        : {result.fit_method}")
    print(f"N                 : {result.n_points}")
    print(f"n_line            : {result.n_line_m_inv:.8e} m^-1")
    print(f"q0                : {result.q0_m_inv:.8e} m^-1")
    print(f"q_edge            : {result.q_edge_m_inv:.8e} m^-1")
    print(f"ell_fit           : {result.ell_fit:.8e}")
    print(f"x1                : {result.x1_m:.8e} m = {result.x1_m*1e6:.6f} um")
    print(f"f_edge            : {result.f_edge_Hz:.8e} Hz")
    print(f"xi                : {result.xi_m:.8e} m")
    print(f"RMSE              : {result.rmse:.8e}")
    print(f"R^2               : {result.r2:.8e}")
    print(f"Wrote outputs to  : {args.outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
