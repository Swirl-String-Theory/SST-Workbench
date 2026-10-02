#!/usr/bin/env python3
"""
sst_ffs_02_filament_projection.py

SST fractional-filament-sea projection tool.

Given a closed filament centreline X(s), compute arc-length parametrization,
curvature kappa(s), Frenet torsion tau(s), a torsion/R-phase signal
u(s)=exp(i phi(s)), the q-spectrum of u(s), and edge diagnostics against
fractional sectors ell = 1,2,4,...

Default run:
    python sst_ffs_02_filament_projection.py --outdir results

CSV curve input:
    python sst_ffs_02_filament_projection.py --curve csv --input curve.csv --outdir results

Physical scaling:
    --unit-scale-m 1e-6      # one input length unit is 1 micrometer
    --length-m 1e-12         # rescale total closed length to 1e-12 m
    --natural-scale          # one curve unit = Gamma0/v_swirl
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

FALLBACK_V_SWIRL = 1.09384563e6       # m s^-1
FALLBACK_R_C = 1.40897017e-15         # m
FALLBACK_RHO_F = 7.0e-7               # kg m^-3
FALLBACK_GAMMA0 = 9.68361918e-9       # m^2 s^-1


def _try_get_attr(obj, names: Iterable[str]) -> Optional[float]:
    for name in names:
        try:
            if isinstance(obj, dict) and name in obj:
                return float(obj[name])
            if hasattr(obj, name):
                value = getattr(obj, name)
                if hasattr(value, "value"):
                    value = value.value
                return float(value)
        except Exception:
            pass
    return None


def load_sst_constants():
    """Best-effort SSTcore import; fallback to canonical constants."""
    v_swirl = FALLBACK_V_SWIRL
    r_c = FALLBACK_R_C
    rho_f = FALLBACK_RHO_F
    gamma0 = FALLBACK_GAMMA0
    source = "fallback canonical constants"

    try:
        import SSTcore as sst  # type: ignore

        candidates = [sst]
        for maybe in ("CONSTANTS", "constants", "canon", "SST_CONSTANTS"):
            if hasattr(sst, maybe):
                candidates.append(getattr(sst, maybe))

        v_names = ("v_swirl", "V_SWIRL", "C_e", "Ce", "v_circlearrowleft", "mathbf_v_circlearrowleft")
        rc_names = ("r_c", "R_c", "rc", "Rc", "core_radius")
        rho_names = ("rho_f", "rho_fluid", "rho_ae_fluid", "rho_effective")
        gamma_names = ("Gamma0", "GAMMA0", "gamma0", "Gamma_0", "circulation")

        for c in candidates:
            v = _try_get_attr(c, v_names)
            if v is not None:
                v_swirl = v
                source = "SSTcore"
                break
        for c in candidates:
            rc = _try_get_attr(c, rc_names)
            if rc is not None:
                r_c = rc
                break
        for c in candidates:
            rho = _try_get_attr(c, rho_names)
            if rho is not None:
                rho_f = rho
                break
        for c in candidates:
            gam = _try_get_attr(c, gamma_names)
            if gam is not None:
                gamma0 = gam
                break
    except Exception:
        pass

    return v_swirl, r_c, rho_f, gamma0, source


# ---------------------------------------------------------------------------
# Geometry generation / loading
# ---------------------------------------------------------------------------


def generate_torus_knot(n: int, p: int = 2, q: int = 3, R: float = 2.0, r: float = 0.75) -> np.ndarray:
    """
    Standard torus knot:
        X(t)=((R+r cos(qt)) cos(pt),
              (R+r cos(qt)) sin(pt),
               r sin(qt))
    Default p=2,q=3 gives a trefoil embedding.
    """
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    x = (R + r * np.cos(q * t)) * np.cos(p * t)
    y = (R + r * np.cos(q * t)) * np.sin(p * t)
    z = r * np.sin(q * t)
    return np.column_stack([x, y, z])


def generate_circle(n: int, radius: float = 1.0) -> np.ndarray:
    t = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    return np.column_stack([radius * np.cos(t), radius * np.sin(t), np.zeros_like(t)])


def load_curve_csv(path: Path) -> np.ndarray:
    """Load named x,y,z columns or the first 3 numeric columns."""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise ValueError(f"Empty curve file: {path}")

    try:
        arr_named = np.genfromtxt(path, delimiter=",", names=True, dtype=float, comments="#")
        if arr_named.dtype.names:
            names = {name.lower(): name for name in arr_named.dtype.names}
            if {"x", "y", "z"}.issubset(names):
                X = np.column_stack([arr_named[names["x"]], arr_named[names["y"]], arr_named[names["z"]]])
                X = X[np.all(np.isfinite(X), axis=1)]
                if len(X) >= 8:
                    return X
    except Exception:
        pass

    for delim in (",", None):
        try:
            data = np.loadtxt(path, delimiter=delim, comments="#")
            data = np.asarray(data, dtype=float)
            if data.ndim == 1:
                data = data.reshape(1, -1)
            if data.shape[1] < 3:
                continue
            X = data[:, :3]
            X = X[np.all(np.isfinite(X), axis=1)]
            if len(X) >= 8:
                return X
        except Exception:
            continue

    raise ValueError(f"Could not parse at least 8 numeric xyz rows from: {path}")


# ---------------------------------------------------------------------------
# Arc length and differential geometry
# ---------------------------------------------------------------------------


def remove_duplicate_closure(X: np.ndarray, tol: float = 1e-12) -> np.ndarray:
    if len(X) > 2 and np.linalg.norm(X[-1] - X[0]) <= tol * max(1.0, np.linalg.norm(X[0])):
        return X[:-1].copy()
    return X.copy()


def periodic_arclength(X: np.ndarray) -> tuple[np.ndarray, float]:
    d = np.linalg.norm(np.roll(X, -1, axis=0) - X, axis=1)
    L = float(np.sum(d))
    s = np.concatenate([[0.0], np.cumsum(d[:-1])])
    return s, L


def resample_closed_curve(X: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray, float]:
    X = remove_duplicate_closure(np.asarray(X, dtype=float))
    if len(X) < 8:
        raise ValueError("Need at least 8 points for a closed filament.")

    s, L = periodic_arclength(X)
    s_ext = np.concatenate([s, [L]])
    X_ext = np.vstack([X, X[0]])

    s_new = np.linspace(0.0, L, n, endpoint=False)
    X_new = np.column_stack([np.interp(s_new, s_ext, X_ext[:, dim]) for dim in range(3)])
    return X_new, s_new, L


def finite_differences_periodic(X: np.ndarray, ds: float):
    r1 = (np.roll(X, -1, axis=0) - np.roll(X, 1, axis=0)) / (2.0 * ds)
    r2 = (np.roll(X, -1, axis=0) - 2.0 * X + np.roll(X, 1, axis=0)) / (ds * ds)
    r3 = (
        np.roll(X, -2, axis=0)
        - 2.0 * np.roll(X, -1, axis=0)
        + 2.0 * np.roll(X, 1, axis=0)
        - np.roll(X, 2, axis=0)
    ) / (2.0 * ds**3)
    return r1, r2, r3


def moving_average_periodic(y: np.ndarray, width: int) -> np.ndarray:
    width = int(width)
    if width <= 1:
        return y.copy()
    if width % 2 == 0:
        width += 1
    pad = width // 2
    yy = np.concatenate([y[-pad:], y, y[:pad]])
    kernel = np.ones(width, dtype=float) / width
    return np.convolve(yy, kernel, mode="valid")


def curvature_torsion(X: np.ndarray, L: float, smooth_width: int = 1):
    n = len(X)
    ds = L / n
    r1, r2, r3 = finite_differences_periodic(X, ds)
    speed = np.linalg.norm(r1, axis=1)
    cross12 = np.cross(r1, r2)
    cross_norm = np.linalg.norm(cross12, axis=1)

    eps = 1e-30
    kappa = cross_norm / np.maximum(speed**3, eps)

    numerator = np.einsum("ij,ij->i", cross12, r3)
    denom = cross_norm**2
    tau = np.zeros_like(kappa)
    scale = max(1.0, float(np.nanmax(denom)))
    mask = denom > 1e-24 * scale
    tau[mask] = numerator[mask] / denom[mask]

    if smooth_width > 1:
        kappa = moving_average_periodic(kappa, smooth_width)
        tau = moving_average_periodic(tau, smooth_width)

    return kappa, tau, r1, r2


def normalize_rows(V: np.ndarray, fallback: Optional[np.ndarray] = None) -> np.ndarray:
    out = np.zeros_like(V, dtype=float)
    norms = np.linalg.norm(V, axis=1)
    good = norms > 1e-30
    out[good] = V[good] / norms[good, None]
    if fallback is None:
        fallback = np.array([1.0, 0.0, 0.0])
    for i in range(len(V)):
        if not good[i]:
            out[i] = out[i - 1] if i > 0 else fallback
    return out


def rodrigues_rotate(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    return (
        v * math.cos(angle)
        + np.cross(axis, v) * math.sin(angle)
        + axis * np.dot(axis, v) * (1.0 - math.cos(angle))
    )


def parallel_transport_frame(T: np.ndarray):
    """Bishop/parallel-transport frame along tangent samples T."""
    n = len(T)
    N = np.zeros_like(T)

    trial_axes = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])]
    a0 = min(trial_axes, key=lambda a: abs(float(np.dot(a, T[0]))))
    N0 = a0 - np.dot(a0, T[0]) * T[0]
    N[0] = N0 / np.linalg.norm(N0)

    for i in range(1, n):
        a = T[i - 1]
        b = T[i]
        axis = np.cross(a, b)
        axis_norm = np.linalg.norm(axis)
        c = float(np.clip(np.dot(a, b), -1.0, 1.0))
        if axis_norm < 1e-14:
            Ni = N[i - 1].copy()
        else:
            axis /= axis_norm
            angle = math.atan2(axis_norm, c)
            Ni = rodrigues_rotate(N[i - 1], axis, angle)

        Ni = Ni - np.dot(Ni, b) * b
        nn = np.linalg.norm(Ni)
        N[i] = Ni / nn if nn > 1e-30 else N[i - 1]

    B = np.cross(T, N)
    B = normalize_rows(B)
    return N, B


def frenet_normal_from_tangent(T: np.ndarray, ds: float):
    dTds = (np.roll(T, -1, axis=0) - np.roll(T, 1, axis=0)) / (2.0 * ds)
    Nf = normalize_rows(dTds)
    Bf = np.cross(T, Nf)
    Bf = normalize_rows(Bf)
    return Nf, Bf


def phase_from_torsion(tau: np.ndarray, L: float) -> np.ndarray:
    n = len(tau)
    ds = L / n
    phi = np.zeros(n, dtype=float)
    phi[1:] = np.cumsum(tau[:-1]) * ds
    return phi


def phase_from_parallel_transport(X: np.ndarray, r1: np.ndarray, L: float) -> np.ndarray:
    n = len(X)
    ds = L / n
    T = normalize_rows(r1)
    N_pt, B_pt = parallel_transport_frame(T)
    N_f, _B_f = frenet_normal_from_tangent(T, ds)

    c = np.einsum("ij,ij->i", N_f, N_pt)
    s = np.einsum("ij,ij->i", N_f, B_pt)
    phi = np.unwrap(np.arctan2(s, c))
    phi -= phi[0]
    return phi


# ---------------------------------------------------------------------------
# Spectral diagnostics
# ---------------------------------------------------------------------------


def fft_spectrum(u: np.ndarray, L: float):
    n = len(u)
    ds = L / n
    q = 2.0 * math.pi * np.fft.fftfreq(n, d=ds)
    U = np.fft.fft(u) / n
    power = np.abs(U) ** 2
    order = np.argsort(q)
    return q[order], power[order]


def weighted_quantile_abs_q(q: np.ndarray, power: np.ndarray, quantile: float) -> float:
    qa = np.abs(q)
    order = np.argsort(qa)
    qa_sorted = qa[order]
    w = power[order]
    total = float(np.sum(w))
    if total <= 0.0:
        return float("nan")
    cdf = np.cumsum(w) / total
    return float(np.interp(quantile, cdf, qa_sorted))


def edge_fraction(q: np.ndarray, power: np.ndarray, q_edge: float) -> float:
    total = float(np.sum(power))
    if total <= 0.0:
        return float("nan")
    return float(np.sum(power[np.abs(q) <= q_edge]) / total)


@dataclass
class Summary:
    curve: str
    n_points: int
    length_m: float
    ds_m: float
    constants_source: str
    v_swirl_m_s: float
    r_c_m: float
    rho_f_kg_m3: float
    gamma0_m2_s: float
    natural_unit_m: float
    q0_m_inv: float
    q_min_m_inv: float
    phase_source: str
    total_torsion_rad: float
    mean_tau_m_inv: float
    rms_tau_m_inv: float
    mean_kappa_m_inv: float
    rms_kappa_m_inv: float
    q_peak_abs_m_inv: float
    q50_abs_m_inv: float
    q90_abs_m_inv: float
    q95_abs_m_inv: float
    ell_eff_95: float
    spectral_m2_power_m_inv2: float


def compute_summary(curve_name, X, L, kappa, tau, phi, q, power, q0, phase_source, constants):
    v_swirl, r_c, rho_f, gamma0, source = constants
    n = len(X)
    ds = L / n
    absq = np.abs(q)
    nonzero = absq > 1e-14 * max(1.0, float(np.max(absq)))
    if np.any(nonzero):
        q_peak = float(absq[nonzero][np.argmax(power[nonzero])])
    else:
        q_peak = 0.0

    p_total = float(np.sum(power))
    spectral_m2 = float(np.sum((q**2) * power) / p_total) if p_total > 0.0 else float("nan")
    q95 = weighted_quantile_abs_q(q, power, 0.95)
    return Summary(
        curve=curve_name,
        n_points=n,
        length_m=float(L),
        ds_m=float(ds),
        constants_source=source,
        v_swirl_m_s=float(v_swirl),
        r_c_m=float(r_c),
        rho_f_kg_m3=float(rho_f),
        gamma0_m2_s=float(gamma0),
        natural_unit_m=float(gamma0 / v_swirl),
        q0_m_inv=float(q0),
        q_min_m_inv=float(2.0 * math.pi / L),
        phase_source=phase_source,
        total_torsion_rad=float(phi[-1] + tau[-1] * ds) if phase_source == "integrated_torsion" else float(phi[-1]),
        mean_tau_m_inv=float(np.mean(tau)),
        rms_tau_m_inv=float(np.sqrt(np.mean(tau**2))),
        mean_kappa_m_inv=float(np.mean(kappa)),
        rms_kappa_m_inv=float(np.sqrt(np.mean(kappa**2))),
        q_peak_abs_m_inv=q_peak,
        q50_abs_m_inv=weighted_quantile_abs_q(q, power, 0.50),
        q90_abs_m_inv=weighted_quantile_abs_q(q, power, 0.90),
        q95_abs_m_inv=q95,
        ell_eff_95=float(q95 / q0) if q0 > 0.0 else float("nan"),
        spectral_m2_power_m_inv2=spectral_m2,
    )


def write_summary_csv(path: Path, summary: Summary, ells: list[int], q: np.ndarray, power: np.ndarray, q0: float, v_swirl: float):
    rows = []
    rows.append({"quantity": "curve", "value": summary.curve, "unit": ""})
    for key, value in asdict(summary).items():
        if key == "curve":
            continue
        unit = ""
        if key.endswith("_m"):
            unit = "m"
        elif key.endswith("_m_s"):
            unit = "m s^-1"
        elif key.endswith("_kg_m3"):
            unit = "kg m^-3"
        elif key.endswith("_m2_s"):
            unit = "m^2 s^-1"
        elif key.endswith("_m_inv"):
            unit = "m^-1"
        elif key.endswith("_m_inv2"):
            unit = "m^-2"
        elif key.endswith("_rad"):
            unit = "rad"
        rows.append({"quantity": key, "value": value, "unit": unit})

    for ell in ells:
        q_edge = ell * q0
        rows.append({"quantity": f"edge_fraction_ell_{ell}", "value": edge_fraction(q, power, q_edge), "unit": "1"})
        rows.append({"quantity": f"q_edge_ell_{ell}", "value": q_edge, "unit": "m^-1"})
        rows.append({"quantity": f"f_edge_ell_{ell}", "value": v_swirl * q_edge / (2.0 * math.pi), "unit": "Hz"})
        rows.append({"quantity": f"x1_ell_{ell}", "value": math.pi / q_edge if q_edge > 0.0 else float("nan"), "unit": "m"})

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["quantity", "value", "unit"])
        writer.writeheader()
        writer.writerows(rows)


def write_spectrum_csv(path: Path, q: np.ndarray, power: np.ndarray):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["q_m_inv", "power"])
        for qi, pi in zip(q, power):
            writer.writerow([f"{qi:.16e}", f"{pi:.16e}"])


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------


def save_geometry_plot(path: Path, X: np.ndarray):
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(X[:, 0], X[:, 1], X[:, 2], linewidth=1.0)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    ax.set_title("Filament centreline")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_torsion_phase_plot(path: Path, s: np.ndarray, kappa: np.ndarray, tau: np.ndarray, phi: np.ndarray):
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(s, kappa, label="kappa(s)")
    ax1.plot(s, tau, label="tau(s)")
    ax1.set_xlabel("s [m]")
    ax1.set_ylabel("curvature/torsion [m^-1]")
    ax1.set_title("Differential geometry along filament")
    ax1.legend()
    fig.tight_layout()
    fig.savefig(path.with_name(path.stem + "_curvature_torsion.png"), dpi=180)
    plt.close(fig)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(s, phi)
    ax.set_xlabel("s [m]")
    ax.set_ylabel("phi(s) [rad]")
    ax.set_title("Filament torsion/R-phase")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_spectrum_plot(path: Path, q: np.ndarray, power: np.ndarray, q0: float, ells: list[int]):
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(q, power, linewidth=1.0)
    ymax = float(np.max(power)) if len(power) else 1.0
    for ell in ells:
        qe = ell * q0
        ax.axvline(qe, linestyle="--", linewidth=0.8)
        ax.axvline(-qe, linestyle="--", linewidth=0.8)
        ax.text(qe, 0.92 * ymax, f"ell={ell}", rotation=90, va="top")
    ax.set_xlabel("q [m^-1]")
    ax.set_ylabel("|U(q)|^2")
    ax.set_title("Spectrum of u(s)=exp(i phi(s))")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", choices=["trefoil", "circle", "csv"], default="trefoil")
    parser.add_argument("--input", type=Path, default=None, help="CSV path when --curve csv.")
    parser.add_argument("--outdir", type=Path, default=Path("sst_ffs_02_results"))

    parser.add_argument("--n", type=int, default=2048, help="Uniform arc-length sample count.")
    parser.add_argument("--smooth-width", type=int, default=7, help="Odd periodic smoothing width for kappa/tau.")

    parser.add_argument("--p", type=int, default=2, help="Torus-knot p for generated trefoil.")
    parser.add_argument("--q", type=int, default=3, help="Torus-knot q for generated trefoil.")
    parser.add_argument("--torus-R", type=float, default=2.0)
    parser.add_argument("--torus-r", type=float, default=0.75)

    parser.add_argument("--unit-scale-m", type=float, default=1.0, help="Meters per input coordinate unit.")
    parser.add_argument("--length-m", type=float, default=None, help="If set, rescale total closed length to this value.")
    parser.add_argument("--natural-scale", action="store_true", help="Use Gamma0/v_swirl meters per input unit.")

    parser.add_argument("--phase-source", choices=["integrated_torsion", "pt_frenet"], default="integrated_torsion")

    parser.add_argument("--q0", type=float, default=None, help="Base q0 in m^-1. Default: q_min=2*pi/L.")
    parser.add_argument("--q0-multiple", type=float, default=1.0, help="q0 = q0_multiple * q_min if --q0 absent.")
    parser.add_argument("--ells", type=int, nargs="+", default=[1, 2, 4])

    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    constants = load_sst_constants()
    v_swirl, r_c, rho_f, gamma0, source = constants

    if args.n < 64:
        raise ValueError("--n should be at least 64 for stable torsion/spectrum estimates.")

    if args.curve == "trefoil":
        X0 = generate_torus_knot(args.n, p=args.p, q=args.q, R=args.torus_R, r=args.torus_r)
        curve_name = f"torus_knot_T({args.p},{args.q})"
    elif args.curve == "circle":
        X0 = generate_circle(args.n)
        curve_name = "circle"
    else:
        if args.input is None:
            raise ValueError("--input is required when --curve csv")
        X0 = load_curve_csv(args.input)
        curve_name = f"csv:{args.input.name}"

    unit_scale = float(args.unit_scale_m)
    if args.natural_scale:
        unit_scale = gamma0 / v_swirl
    X0 = X0 * unit_scale

    X, s, L = resample_closed_curve(X0, args.n)

    if args.length_m is not None:
        scale = float(args.length_m) / L
        X = X * scale
        X, s, L = resample_closed_curve(X, args.n)

    ds = L / args.n
    kappa, tau, r1, _r2 = curvature_torsion(X, L, smooth_width=args.smooth_width)

    phi_integrated = phase_from_torsion(tau, L)
    phi_pt = phase_from_parallel_transport(X, r1, L)

    phi = phi_integrated if args.phase_source == "integrated_torsion" else phi_pt

    u = np.exp(1j * phi)
    u_centered = u - np.mean(u)
    qspec, power = fft_spectrum(u_centered, L)

    q_min = 2.0 * math.pi / L
    q0 = float(args.q0) if args.q0 is not None else float(args.q0_multiple * q_min)

    summary = compute_summary(curve_name, X, L, kappa, tau, phi, qspec, power, q0, args.phase_source, constants)

    args.outdir.mkdir(parents=True, exist_ok=True)
    write_summary_csv(args.outdir / "sst_ffs_02_summary.csv", summary, args.ells, qspec, power, q0, v_swirl)
    write_spectrum_csv(args.outdir / "sst_ffs_02_spectrum.csv", qspec, power)

    with (args.outdir / "sst_ffs_02_curve_fields.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["s_m", "x_m", "y_m", "z_m", "kappa_m_inv", "tau_m_inv", "phi_integrated_rad", "phi_pt_rad"])
        for si, xi, ki, ti, phii, phipti in zip(s, X, kappa, tau, phi_integrated, phi_pt):
            writer.writerow([
                f"{si:.16e}", f"{xi[0]:.16e}", f"{xi[1]:.16e}", f"{xi[2]:.16e}",
                f"{ki:.16e}", f"{ti:.16e}", f"{phii:.16e}", f"{phipti:.16e}",
            ])

    if not args.no_plots:
        save_geometry_plot(args.outdir / "sst_ffs_02_geometry.png", X)
        save_torsion_phase_plot(args.outdir / "sst_ffs_02_phase.png", s, kappa, tau, phi)
        save_spectrum_plot(args.outdir / "sst_ffs_02_spectrum.png", qspec, power, q0, args.ells)

    print(f"SST constants source: {source}")
    print(f"curve             : {summary.curve}")
    print(f"N                 : {summary.n_points}")
    print(f"L                 : {summary.length_m:.8e} m")
    print(f"ds                : {summary.ds_m:.8e} m")
    print(f"v_swirl           : {summary.v_swirl_m_s:.8e} m s^-1")
    print(f"r_c               : {summary.r_c_m:.8e} m")
    print(f"Gamma0/v_swirl    : {summary.natural_unit_m:.8e} m")
    print(f"phase source      : {summary.phase_source}")
    print(f"total torsion     : {summary.total_torsion_rad:.8e} rad")
    print(f"<kappa>           : {summary.mean_kappa_m_inv:.8e} m^-1")
    print(f"rms(kappa)        : {summary.rms_kappa_m_inv:.8e} m^-1")
    print(f"<tau>             : {summary.mean_tau_m_inv:.8e} m^-1")
    print(f"rms(tau)          : {summary.rms_tau_m_inv:.8e} m^-1")
    print(f"q_min             : {summary.q_min_m_inv:.8e} m^-1")
    print(f"q0                : {summary.q0_m_inv:.8e} m^-1")
    print(f"q_peak_abs        : {summary.q_peak_abs_m_inv:.8e} m^-1")
    print(f"q95_abs           : {summary.q95_abs_m_inv:.8e} m^-1")
    print(f"ell_eff_95        : {summary.ell_eff_95:.8e}")
    print(f"<q^2>_power       : {summary.spectral_m2_power_m_inv2:.8e} m^-2")
    print()
    print("ell | q_edge [m^-1] | f_edge [Hz] | x1 [m] | contained spectral power")
    for ell in args.ells:
        qe = ell * q0
        fe = v_swirl * qe / (2.0 * math.pi)
        x1 = math.pi / qe if qe > 0.0 else float("nan")
        frac = edge_fraction(qspec, power, qe)
        print(f"{ell:>3d} | {qe:>13.6e} | {fe:>11.6e} | {x1:>11.6e} | {frac:>10.6f}")

    print()
    print(f"Wrote outputs to: {args.outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
