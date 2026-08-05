#!/usr/bin/env python3
"""
sst_ffs_01_rosetta_spectrum.py

Fractional-Fermi-sea / SST Rosetta calculator.

Computes the ideal fractional filament-sea model

    theta_l(q) = (1/l) * Theta(l*q0 - |q|)

with:
    N_line = q0/pi
    M2_l   = l^2 q0^3 / (3*pi)
    G1_l(s)= sin(l*q0*s)/(l*q0*s)
    f_l    = v_swirl * l*q0 / (2*pi)

The script works without SSTcore, but tries to read canonical constants from
SSTcore if it is importable.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np


# --- Canonical fallback constants ---
FALLBACK_V_SWIRL = 1.09384563e6       # m s^-1
FALLBACK_R_C = 1.40897017e-15         # m
FALLBACK_RHO_F = 7.0e-7               # kg m^-3


def _try_get_attr(obj, names: Iterable[str]) -> Optional[float]:
    """Try several attribute names or dict keys and return a float if found."""
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
    """
    Best-effort SSTcore import.

    This intentionally avoids assuming one fixed SSTcore API. It checks common
    module-level names and a possible CONSTANTS/constants mapping.
    """
    v_swirl = FALLBACK_V_SWIRL
    r_c = FALLBACK_R_C
    rho_f = FALLBACK_RHO_F
    source = "fallback canonical constants"

    try:
        import SSTcore as sst  # type: ignore

        candidates = [sst]
        for maybe in ("CONSTANTS", "constants", "canon", "SST_CONSTANTS"):
            if hasattr(sst, maybe):
                candidates.append(getattr(sst, maybe))

        v_names = (
            "v_swirl",
            "V_SWIRL",
            "C_e",
            "Ce",
            "v_circlearrowleft",
            "mathbf_v_circlearrowleft",
        )
        rc_names = ("r_c", "R_c", "rc", "Rc", "core_radius")
        rho_names = ("rho_f", "rho_fluid", "rho_ae_fluid", "rho_effective")

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

    except Exception:
        pass

    return v_swirl, r_c, rho_f, source


@dataclass(frozen=True)
class FFSRow:
    ell: int
    q0_m_inv: float
    q_edge_m_inv: float
    n_line_m_inv: float
    m2_m_inv3: float
    x1_m: float
    f_edge_hz: float
    omega_edge_rad_s: float


def theta(q: np.ndarray, ell: int, q0: float) -> np.ndarray:
    """Ideal fractional occupancy theta_l(q)."""
    return np.where(np.abs(q) <= ell * q0, 1.0 / ell, 0.0)


def g1(s: np.ndarray, ell: int, q0: float) -> np.ndarray:
    """Normalized ideal one-body / phase correlator."""
    q_edge = ell * q0
    return np.sinc(q_edge * s / math.pi)  # np.sinc(x)=sin(pi*x)/(pi*x)


def ffs_row(ell: int, n_line_m_inv: float, v_swirl: float) -> FFSRow:
    """Analytic ideal FFS/SST Rosetta observables for one ell-sector."""
    q0 = math.pi * n_line_m_inv
    q_edge = ell * q0
    m2 = ell**2 * q0**3 / (3.0 * math.pi)
    x1 = math.pi / q_edge
    omega = v_swirl * q_edge
    f = omega / (2.0 * math.pi)
    return FFSRow(
        ell=ell,
        q0_m_inv=q0,
        q_edge_m_inv=q_edge,
        n_line_m_inv=n_line_m_inv,
        m2_m_inv3=m2,
        x1_m=x1,
        f_edge_hz=f,
        omega_edge_rad_s=omega,
    )


def write_csv(rows: list[FFSRow], out_csv: Path) -> None:
    header = (
        "ell,q0_m_inv,q_edge_m_inv,n_line_m_inv,"
        "M2_m_inv3,x1_m,f_edge_Hz,omega_edge_rad_s\n"
    )
    lines = [header]
    for r in rows:
        lines.append(
            f"{r.ell},{r.q0_m_inv:.16e},{r.q_edge_m_inv:.16e},"
            f"{r.n_line_m_inv:.16e},{r.m2_m_inv3:.16e},"
            f"{r.x1_m:.16e},{r.f_edge_hz:.16e},"
            f"{r.omega_edge_rad_s:.16e}\n"
        )
    out_csv.write_text("".join(lines), encoding="utf-8")


def write_g1_plot(ells: list[int], q0: float, out_png: Path) -> None:
    import matplotlib.pyplot as plt

    s = np.linspace(0.0, 4.0e-6, 1200)

    plt.figure()
    for ell in ells:
        plt.plot(s * 1e6, g1(s, ell, q0), label=f"ell={ell}")

    plt.axhline(0.0, linewidth=0.8)
    plt.xlabel("s [micrometer]")
    plt.ylabel("G1_l(s)")
    plt.title("Ideal fractional filament-sea correlator")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-line-um-inv",
        type=float,
        default=0.5,
        help="Line density in micrometer^-1. Default: 0.5 um^-1.",
    )
    parser.add_argument(
        "--ells",
        type=int,
        nargs="+",
        default=[1, 2, 4],
        help="Fractional sectors to compute. Default: 1 2 4.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("."),
        help="Output directory.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip PNG plot generation.",
    )
    args = parser.parse_args()

    v_swirl, r_c, rho_f, source = load_sst_constants()

    n_line = args.n_line_um_inv * 1.0e6  # um^-1 -> m^-1
    rows = [ffs_row(ell, n_line, v_swirl) for ell in args.ells]

    args.outdir.mkdir(parents=True, exist_ok=True)
    out_csv = args.outdir / "sst_ffs_rosetta_table.csv"
    write_csv(rows, out_csv)

    q0 = math.pi * n_line
    out_png = args.outdir / "sst_ffs_g1.png"
    if not args.no_plot:
        write_g1_plot(args.ells, q0, out_png)

    print(f"SST constants source: {source}")
    print(f"v_swirl = {v_swirl:.8e} m s^-1")
    print(f"r_c     = {r_c:.8e} m")
    print(f"rho_f   = {rho_f:.8e} kg m^-3")
    print(f"n_line  = {n_line:.8e} m^-1")
    print(f"q0      = {q0:.8e} m^-1")
    print()
    print(
        "ell | q_edge [m^-1] | x1 [um] | f_edge [Hz] | "
        "M2 [m^-3] | M2/M2_ell1"
    )
    m2_ref = rows[0].m2_m_inv3 if rows else float("nan")
    for r in rows:
        print(
            f"{r.ell:>3d} | {r.q_edge_m_inv:>13.6e} | "
            f"{r.x1_m*1e6:>7.4f} | {r.f_edge_hz:>12.6e} | "
            f"{r.m2_m_inv3:>12.6e} | {r.m2_m_inv3/m2_ref:>10.6f}"
        )

    print()
    print(f"Wrote: {out_csv}")
    if not args.no_plot:
        print(f"Wrote: {out_png}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
