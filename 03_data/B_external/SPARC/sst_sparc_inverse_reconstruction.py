#!/usr/bin/env python3
"""
SST SPARC inverse reconstruction
================================

Purpose
-------
Compute inverse SST line-fabric diagnostics from SPARC galaxies.

The script keeps two distinct quantities separate:

1. Rotation-amplitude coherent line count
   C_A_obs = 2*pi*R_bar*v_flat^2 / (Gamma0*v_swirl)

   This is reconstructed directly from the observed flat velocity and an
   adopted baryonic radius R_bar.

2. L_PV alignment coherence multiplier
   C_Lambda_req = Lambda_target / Lambda_local

   This is the collective multiplier required for the local parity-odd
   helicity source to reach the target line-fabric alignment strength.

These two quantities are NOT the same object. Keeping them separated avoids
accidentally mixing the rotation-curve amplitude closure with the local
L_PV torque closure.

Data
----
Uses official SPARC table files when --download is passed:
- SPARC_Lelli2016c.mrt
- MassModels_Lelli2016c.mrt

The sample table supplies Galaxy, L[3.6], MHI, RHI, Rdisk, Vflat, Q.
The mass-model table supplies radial data: R, Vobs, e_Vobs, Vgas, Vdisk, Vbul.

Dependencies
------------
Only Python standard library + numpy + pandas.

Example
-------
python sst_sparc_inverse_reconstruction.py --download --quality-max 2 --rbar-mode RHI \
  --out sparc_sst_inverse.csv

python sst_sparc_inverse_reconstruction.py --table1 SPARC_Lelli2016c.mrt \
  --table2 MassModels_Lelli2016c.mrt --rbar-mode Rlast
"""

from __future__ import annotations

import argparse
import math
import sys
import urllib.request
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# -----------------------------
# Canonical SST / physical constants
# -----------------------------

C_LIGHT = 2.99792458e8                         # m s^-1
HBAR = 1.054571817e-34                         # J s
G_NEWTON = 6.67430e-11                         # m^3 kg^-1 s^-2
M_E = 9.1093837015e-31                         # kg
M_N = 1.67492749804e-27                        # kg, neutron mass as nucleon proxy
M_SUN = 1.98847e30                             # kg
KPC = 3.0856775814913673e19                    # m
PC = 3.0856775814913673e16                     # m

ALPHA = 7.2973525693e-3
ALPHA_G = G_NEWTON * M_E**2 / (HBAR * C_LIGHT)

V_SWIRL = 1.09384563e6                         # m s^-1
R_C = 1.40897017e-15                           # m
RHO_F = 7.0e-7                                 # kg m^-3
RHO_CORE = 3.8934358266918687e18               # kg m^-3

GAMMA_0 = 2.0 * math.pi * R_C * V_SWIRL        # m^2 s^-1

EPS_G = 4.0 * ALPHA_G / ALPHA
R_TENSION = 1.0 / EPS_G


SPARC_TABLE1_URL = "https://astroweb.cwru.edu/SPARC/SPARC_Lelli2016c.mrt"
SPARC_TABLE2_URL = "https://astroweb.cwru.edu/SPARC/MassModels_Lelli2016c.mrt"


# -----------------------------
# Download helpers
# -----------------------------

def download_file(url: str, path: Path, overwrite: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return path
    print(f"Downloading {url} -> {path}", file=sys.stderr)
    urllib.request.urlretrieve(url, path)
    return path


# -----------------------------
# MRT fixed-width parsers
# -----------------------------

def _to_float(s: str) -> float:
    s = s.strip()
    if not s or s in {"...", "---", "nan", "NaN"}:
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def _to_int(s: str) -> int | float:
    s = s.strip()
    if not s or s in {"...", "---", "nan", "NaN"}:
        return np.nan
    try:
        return int(s)
    except ValueError:
        return np.nan


def parse_sparc_table1(path: Path) -> pd.DataFrame:
    """
    Parse SPARC_Lelli2016c.mrt using byte definitions advertised in the MRT header.

    Byte columns, converted from 1-indexed inclusive to Python slices:
    Galaxy 0:11, T 11:13, D 13:19, e_D 19:24, f_D 24:26,
    Inc 26:30, e_Inc 30:34, L36 34:41, e_L36 41:48,
    Reff 48:53, SBeff 53:61, Rdisk 61:66, SBdisk 66:74,
    MHI 74:81, RHI 81:86, Vflat 86:91, e_Vflat 91:96, Q 96:99, Ref 99:113.
    """
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if len(line) < 99:
            continue
        vflat = _to_float(line[86:91])
        q = _to_int(line[96:99])
        galaxy = line[0:11].strip()
        if not galaxy or not np.isfinite(vflat) or not np.isfinite(q):
            continue
        if galaxy.lower().startswith(("title", "byte", "galaxy")):
            continue
        rows.append({
            "Galaxy": galaxy,
            "T": _to_int(line[11:13]),
            "D_Mpc": _to_float(line[13:19]),
            "e_D_Mpc": _to_float(line[19:24]),
            "f_D": _to_int(line[24:26]),
            "Inc_deg": _to_float(line[26:30]),
            "e_Inc_deg": _to_float(line[30:34]),
            "L36_1e9_Lsun": _to_float(line[34:41]),
            "e_L36_1e9_Lsun": _to_float(line[41:48]),
            "Reff_kpc": _to_float(line[48:53]),
            "SBeff_Lsun_pc2": _to_float(line[53:61]),
            "Rdisk_kpc": _to_float(line[61:66]),
            "SBdisk_Lsun_pc2": _to_float(line[66:74]),
            "MHI_1e9_Msun": _to_float(line[74:81]),
            "RHI_kpc": _to_float(line[81:86]),
            "Vflat_kms": vflat,
            "e_Vflat_kms": _to_float(line[91:96]),
            "Q": int(q),
            "Ref": line[99:113].strip(),
        })
    if not rows:
        raise RuntimeError(f"No SPARC Table1 data rows parsed from {path}")
    return pd.DataFrame(rows)


def parse_sparc_table2(path: Path) -> pd.DataFrame:
    """
    Parse MassModels_Lelli2016c.mrt using byte definitions advertised in the MRT header.

    Columns:
    ID 0:11, D 12:18, R 19:25, Vobs 26:32, e_Vobs 33:38,
    Vgas 39:45, Vdisk 46:52, Vbul 53:59, SBdisk 60:67, SBbul 68:76.
    """
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        if len(line) < 59:
            continue
        galaxy = line[0:11].strip()
        r = _to_float(line[19:25])
        vobs = _to_float(line[26:32])
        if not galaxy or not np.isfinite(r) or not np.isfinite(vobs):
            continue
        if galaxy.lower().startswith(("title", "bytes", "id", "table")):
            continue
        rows.append({
            "Galaxy": galaxy,
            "D_Mpc_mm": _to_float(line[12:18]),
            "R_kpc": r,
            "Vobs_kms": vobs,
            "e_Vobs_kms": _to_float(line[33:38]),
            "Vgas_kms": _to_float(line[39:45]),
            "Vdisk_kms": _to_float(line[46:52]),
            "Vbul_kms": _to_float(line[53:59]),
            "SBdisk_Lsun_pc2_mm": _to_float(line[60:67]),
            "SBbul_Lsun_pc2_mm": _to_float(line[68:76]) if len(line) >= 76 else np.nan,
        })
    if not rows:
        raise RuntimeError(f"No SPARC Table2 mass-model rows parsed from {path}")
    return pd.DataFrame(rows)


# -----------------------------
# SST inverse reconstruction
# -----------------------------

def estimate_mbar_kg(df: pd.DataFrame, upsilon_star: float, gas_factor: float) -> pd.Series:
    """
    Approximate baryonic mass from SPARC sample table:
    Mbar = upsilon_star * L[3.6] + gas_factor * MHI.

    Units in table are 10^9 Lsun and 10^9 Msun, returned in kg.

    Caveat:
    This is a pragmatic first-pass estimator. A more precise baryon model should
    use disk/bulge decompositions and mass-model fits.
    """
    stellar_msun = upsilon_star * df["L36_1e9_Lsun"] * 1.0e9
    gas_msun = gas_factor * df["MHI_1e9_Msun"] * 1.0e9
    return (stellar_msun + gas_msun) * M_SUN


def choose_rbar_kpc(sample: pd.DataFrame, mass_models: Optional[pd.DataFrame], mode: str) -> pd.Series:
    mode = mode.lower()
    if mode == "rhi":
        return sample["RHI_kpc"]
    if mode == "rdisk":
        return sample["Rdisk_kpc"]
    if mode == "reff":
        return sample["Reff_kpc"]
    if mode == "rflat":
        return sample["RHI_kpc"]
    if mode == "rlast":
        if mass_models is None or mass_models.empty:
            raise ValueError("--rbar-mode Rlast requires Table2 mass-model data")
        rlast = mass_models.groupby("Galaxy", as_index=True)["R_kpc"].max()
        return sample["Galaxy"].map(rlast)
    raise ValueError(f"Unknown rbar mode: {mode}")


def estimate_vflat_kms(sample: pd.DataFrame, mass_models: Optional[pd.DataFrame]) -> pd.Series:
    """
    Prefer SPARC Vflat. If Vflat <= 0 or missing, estimate from the outer three Vobs points.
    """
    v = sample["Vflat_kms"].copy()
    bad = ~np.isfinite(v) | (v <= 0)
    if bad.any() and mass_models is not None and not mass_models.empty:
        outer = (
            mass_models.sort_values(["Galaxy", "R_kpc"])
            .groupby("Galaxy")
            .tail(3)
            .groupby("Galaxy")["Vobs_kms"]
            .mean()
        )
        v.loc[bad] = sample.loc[bad, "Galaxy"].map(outer)
    return v


def local_lpv_lambda(rho: float, g5: float, j5: float, volume_factor: float) -> float:
    """
    Local L_PV alignment strength:
        Lambda_local = g5 J5 rho v_swirl^2 Vchi m_n r_c^2 / hbar^2
    with Vchi = volume_factor * pi r_c^3.

    Default volume_factor=1 corresponds to Vchi=pi r_c^3.
    """
    vchi = volume_factor * math.pi * R_C**3
    return g5 * j5 * rho * V_SWIRL**2 * vchi * M_N * R_C**2 / HBAR**2


def reconstruct(
    sample: pd.DataFrame,
    mass_models: Optional[pd.DataFrame],
    rbar_mode: str,
    upsilon_star: float,
    gas_factor: float,
    quality_max: int,
    p_chi: float,
    rho_mode: str,
    g5: float,
    j5: float,
    volume_factor: float,
) -> pd.DataFrame:
    df = sample.copy()

    df = df[np.isfinite(df["Q"]) & (df["Q"] <= quality_max)].copy()

    df["Mbar_kg"] = estimate_mbar_kg(df, upsilon_star=upsilon_star, gas_factor=gas_factor)
    df["N_baryon"] = df["Mbar_kg"] / M_N

    df["Rbar_kpc"] = choose_rbar_kpc(df, mass_models, rbar_mode)
    df["Vflat_used_kms"] = estimate_vflat_kms(df, mass_models)

    good = (
        np.isfinite(df["Mbar_kg"]) & (df["Mbar_kg"] > 0) &
        np.isfinite(df["N_baryon"]) & (df["N_baryon"] > 0) &
        np.isfinite(df["Rbar_kpc"]) & (df["Rbar_kpc"] > 0) &
        np.isfinite(df["Vflat_used_kms"]) & (df["Vflat_used_kms"] > 0)
    )
    df = df[good].copy()

    r_m = df["Rbar_kpc"] * KPC
    v_mps = df["Vflat_used_kms"] * 1.0e3

    df["A_chi_obs_m2_s2"] = v_mps**2

    # Rotation-amplitude coherent-line count.
    df["C_A_obs"] = 2.0 * math.pi * r_m * v_mps**2 / (GAMMA_0 * V_SWIRL)
    df["f_A_obs"] = df["C_A_obs"] / df["N_baryon"]
    df["H_A_eff_m"] = R_C * np.sqrt(df["C_A_obs"])
    df["H_A_eff_AU"] = df["H_A_eff_m"] / 1.495978707e11
    df["H_A_eff_pc"] = df["H_A_eff_m"] / PC

    # Target alignment strength for selected p_chi.
    df["epsilon_g"] = EPS_G
    df["R_tension"] = R_TENSION
    df["p_chi"] = p_chi
    df["Lambda_target"] = R_TENSION**p_chi
    df["theta_rms_rad"] = np.sqrt(2.0 / df["Lambda_target"])
    df["epsilon_z"] = 1.0 / df["Lambda_target"]

    if rho_mode.lower() == "core":
        rho = RHO_CORE
    elif rho_mode.lower() in {"f", "fluid", "rho_f"}:
        rho = RHO_F
    else:
        raise ValueError("--rho-mode must be 'core' or 'fluid'")

    lambda_local = local_lpv_lambda(rho=rho, g5=g5, j5=j5, volume_factor=volume_factor)
    df["Lambda_local_LPV"] = lambda_local

    # Required collective multiplier for L_PV alignment closure.
    df["C_Lambda_req"] = df["Lambda_target"] / lambda_local
    df["f_Lambda_req"] = df["C_Lambda_req"] / df["N_baryon"]
    df["H_Lambda_eff_m"] = R_C * np.sqrt(df["C_Lambda_req"])
    df["H_Lambda_eff_AU"] = df["H_Lambda_eff_m"] / 1.495978707e11
    df["H_Lambda_eff_pc"] = df["H_Lambda_eff_m"] / PC

    df["C_A_over_C_Lambda"] = df["C_A_obs"] / df["C_Lambda_req"]

    return df.sort_values("Galaxy").reset_index(drop=True)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "C_A_obs", "f_A_obs", "H_A_eff_AU", "H_A_eff_pc",
        "C_Lambda_req", "f_Lambda_req", "H_Lambda_eff_AU", "H_Lambda_eff_pc",
        "C_A_over_C_Lambda",
    ]
    rows = []
    for c in cols:
        s = df[c].replace([np.inf, -np.inf], np.nan).dropna()
        if len(s) == 0:
            continue
        rows.append({
            "quantity": c,
            "n": len(s),
            "median": s.median(),
            "mean": s.mean(),
            "std": s.std(),
            "p16": s.quantile(0.16),
            "p84": s.quantile(0.84),
            "min": s.min(),
            "max": s.max(),
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="SST inverse reconstruction on SPARC galaxies")
    parser.add_argument("--data-dir", default="sparc_data", help="Directory for downloaded or local SPARC files")
    parser.add_argument("--download", action="store_true", help="Download official SPARC .mrt files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite downloaded files")
    parser.add_argument("--table1", default=None, help="Path to SPARC_Lelli2016c.mrt")
    parser.add_argument("--table2", default=None, help="Path to MassModels_Lelli2016c.mrt")
    parser.add_argument("--out", default="sparc_sst_inverse.csv", help="Output CSV path")
    parser.add_argument("--summary-out", default="sparc_sst_inverse_summary.csv", help="Output summary CSV path")

    parser.add_argument("--quality-max", type=int, default=2, help="Maximum SPARC quality flag Q to include")
    parser.add_argument("--rbar-mode", default="RHI", choices=["RHI", "Rdisk", "Reff", "Rlast", "Rflat"],
                        help="Radius used as R_bar")
    parser.add_argument("--upsilon-star", type=float, default=0.5,
                        help="Stellar mass-to-light ratio at 3.6 micron")
    parser.add_argument("--gas-factor", type=float, default=1.33,
                        help="HI gas multiplier for helium correction")
    parser.add_argument("--p-chi", type=float, default=4.0/3.0,
                        help="Alignment exponent p_chi in Lambda_target = R_tension^p_chi")
    parser.add_argument("--rho-mode", default="core", choices=["core", "fluid"],
                        help="Density used for local L_PV estimate")
    parser.add_argument("--g5", type=float, default=1.0, help="Dimensionless parity-odd coupling")
    parser.add_argument("--j5", type=float, default=1.0, help="Dimensionless chirality source factor")
    parser.add_argument("--volume-factor", type=float, default=1.0,
                        help="Vchi = volume_factor*pi*r_c^3")

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if args.download:
        table1 = download_file(SPARC_TABLE1_URL, data_dir / "SPARC_Lelli2016c.mrt", args.overwrite)
        table2 = download_file(SPARC_TABLE2_URL, data_dir / "MassModels_Lelli2016c.mrt", args.overwrite)
    else:
        table1 = Path(args.table1) if args.table1 is not None else data_dir / "SPARC_Lelli2016c.mrt"
        table2 = Path(args.table2) if args.table2 is not None else data_dir / "MassModels_Lelli2016c.mrt"

    if not table1.exists():
        raise FileNotFoundError(f"Missing Table1 file: {table1}. Use --download or --table1.")
    if not table2.exists() and args.rbar_mode.lower() == "rlast":
        raise FileNotFoundError(f"Missing Table2 file: {table2}. Rlast needs --download or --table2.")

    print(f"Parsing {table1}", file=sys.stderr)
    sample = parse_sparc_table1(table1)

    mass_models = None
    if table2.exists():
        print(f"Parsing {table2}", file=sys.stderr)
        try:
            mass_models = parse_sparc_table2(table2)
        except RuntimeError as exc:
            print(f"WARNING: {exc}", file=sys.stderr)
            mass_models = None

    result = reconstruct(
        sample=sample,
        mass_models=mass_models,
        rbar_mode=args.rbar_mode,
        upsilon_star=args.upsilon_star,
        gas_factor=args.gas_factor,
        quality_max=args.quality_max,
        p_chi=args.p_chi,
        rho_mode=args.rho_mode,
        g5=args.g5,
        j5=args.j5,
        volume_factor=args.volume_factor,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)

    summary = summarize(result)
    summary_out = Path(args.summary_out)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_out, index=False)

    print("\nSST / SPARC inverse reconstruction complete.")
    print(f"Galaxies used: {len(result)}")
    print(f"Output:  {out}")
    print(f"Summary: {summary_out}")
    print("\nKey constants:")
    print(f"  Gamma0      = {GAMMA_0:.8e} m^2/s")
    print(f"  epsilon_g   = {EPS_G:.8e}")
    print(f"  R_tension   = {R_TENSION:.8e}")
    print(f"  Lambda p={args.p_chi:.6g} = {R_TENSION**args.p_chi:.8e}")
    print(f"  Lambda_local_LPV ({args.rho_mode}) = "
          f"{local_lpv_lambda(RHO_CORE if args.rho_mode=='core' else RHO_F, args.g5, args.j5, args.volume_factor):.8e}")
    print("\nMedian diagnostics:")
    with pd.option_context("display.max_columns", None, "display.width", 180):
        print(summary[["quantity", "n", "median", "p16", "p84"]].to_string(index=False))


if __name__ == "__main__":
    main()
