#!/usr/bin/env python3
"""
SST-Proof_On_Attosecond_Chiral_Photoionization_Dynamics.py

Numerical checks for the SST interpretation of attosecond chiral photoionization.
- Maps delays (as) to effective path differences (Å) across representative electron energies.
- Estimates the negligible swirl-time dilation contribution per 2ω period.
- Provides optional CSV export and human-readable stdout tables.

Author: Omar Iskandarani
License: CC-BY 4.0 (adjust if needed)
"""

from __future__ import annotations
import math
import argparse
from typing import List
import pandas as pd

# Optional UI display (ignored if not available)
try:
    from ace_tools import display_dataframe_to_user  # type: ignore
except Exception:  # pragma: no cover
    display_dataframe_to_user = None  # type: ignore

# ---- Physical constants (SI) ----
C = 299_792_458.0                 # m/s, speed of light
ME = 9.109_383_7015e-31           # kg, electron mass (CODATA 2018/2022)
EV = 1.602_176_634e-19            # J, 1 eV in joules

def electron_speed(E_eV: float) -> float:
    """Nonrelativistic electron speed sqrt(2E/m)."""
    return math.sqrt(2.0 * E_eV * EV / ME)

def path_difference(v: float, dt: float) -> float:
    """Δℓ = v * Δt (meters)."""
    return v * dt

def dilation_shift_per_period(v: float, T: float) -> float:
    """Δt_dil = T * (1 - sqrt(1 - (v/c)^2)) (seconds)."""
    beta2 = (v / C) ** 2
    return T * (1.0 - math.sqrt(max(0.0, 1.0 - beta2)))

def beta_required_for_delay(delta_t: float, T: float) -> float:
    """Solve 1 - sqrt(1 - β^2) = Δt/T  => β = sqrt(1 - (1 - Δ)^2)."""
    d = delta_t / T
    val = 1.0 - (1.0 - d) ** 2
    return math.sqrt(max(0.0, val))

def compute_path_table(energies_eV, delays_as, T_rabbit_s) -> pd.DataFrame:
    rows = []
    for E in energies_eV:
        v = electron_speed(E)
        for d_as in delays_as:
            d_s = d_as * 1e-18
            dL = path_difference(v, d_s)
            rows.append({
                "E (eV)": E,
                "v_e (m/s)": v,
                "Delay (as)": d_as,
                "Δℓ (nm)": dL * 1e9,
                "Δℓ (Å)": dL * 1e10,
                "Phase frac Δτ/T": d_s / T_rabbit_s,
                "Phase shift (deg)": 360.0 * d_s / T_rabbit_s,
            })
    return pd.DataFrame(rows)

def compute_dilation_table(vswirl: float, T_rabbit_s: float) -> pd.DataFrame:
    dt = dilation_shift_per_period(vswirl, T_rabbit_s)
    out = {
        "vswirl (m/s)": vswirl,
        "β_s (vswirl/c)": vswirl / C,
        "Δt_dil per 1.33 fs (as)": dt * 1e18,
        "β required for 60 as": beta_required_for_delay(60e-18, T_rabbit_s),
        "v required for 60 as (m/s)": beta_required_for_delay(60e-18, T_rabbit_s) * C,
        "β required for 240 as": beta_required_for_delay(240e-18, T_rabbit_s),
        "v required for 240 as (m/s)": beta_required_for_delay(240e-18, T_rabbit_s) * C,
    }
    return pd.DataFrame([out])

def main():
    ap = argparse.ArgumentParser(description="SST numerical checks for attosecond chiral photoionization.")
    ap.add_argument("--energies", type=str, default="2,4,6,8,10,12",
                    help="Comma-separated electron kinetic energies in eV (default: 2,4,6,8,10,12)")
    ap.add_argument("--delays", type=str, default="60,240",
                    help="Comma-separated delays in attoseconds (default: 60,240)")
    ap.add_argument("--Tfs", type=float, default=1.33,
                    help="RABBIT 2ω period in femtoseconds (default: 1.33)")
    ap.add_argument("--vswirl", type=float, default=1_093_845.63,
                    help="Canonical swirl speed in m/s (default: 1,093,845.63)")
    ap.add_argument("--csv-prefix", type=str, default="",
                    help="If set, write CSVs with this prefix (e.g., 'sst_checks' -> sst_checks_paths.csv).")
    args = ap.parse_args()

    energies = [float(x) for x in args.energies.split(",") if x.strip()]
    delays = [float(x) for x in args.delays.split(",") if x.strip()]
    T_rabbit_s = args.Tfs * 1e-15

    df_paths = compute_path_table(energies, delays, T_rabbit_s)
    df_dilation = compute_dilation_table(args.vswirl, T_rabbit_s)

    # Console preview
    with pd.option_context("display.max_columns", None, "display.width", 120):
        print("\n=== SST: Delay → Path mapping ===")
        print(df_paths.head(10))
        print("\n=== SST: Swirl dilation sanity check ===")
        print(df_dilation)

    # Optional CSVs
    if args.csv_prefix:
        df_paths.to_csv(f"{args.csv_prefix}_paths.csv", index=False)
        df_dilation.to_csv(f"{args.csv_prefix}_dilation.csv", index=False)
        print(f"\nWrote {args.csv_prefix}_paths.csv and {args.csv_prefix}_dilation.csv")

    # Optional notebook/table display
    if display_dataframe_to_user:
        try:
            display_dataframe_to_user("SST_attosecond_paths", df_paths)
            display_dataframe_to_user("SST_swirl_dilation_check", df_dilation)
        except Exception:
            pass

if __name__ == "__main__":
    main()
