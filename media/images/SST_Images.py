#!/usr/bin/env python3
"""
regen_sst_plots.py
Regenerate canonical SST / Swirl-String Theory profiles (Omega, v_theta, dynamic pressure, time dilation)
Created for: Omar Iskandarani — SST Canon v0.3.1

Dependencies:
    pip install numpy matplotlib pandas

Usage:
    python regen_sst_plots.py
    # optional args:
    python regen_sst_plots.py --outdir ./figs --rmin 1e-18 --rmax 1e-12 --npts 300
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
# Use 'Agg' backend for headless servers if needed:
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -----------------------
# Canonical constants (SST Canon v0.3.1)
# -----------------------
VS = 1.09384563e6         # |v_{circlearrowleft}|, m/s
RC = 1.40897017e-15       # r_c, m
RHO_F = 7.0e-7            # rho_f, kg/m^3
ALPHA = 7.29735e-3        # fine structure (approx)
PHI = (1.0 + 5.0**0.5) / 2.0
C = 2.99792e8             # speed of light (canonical), m/s

# -----------------------
# Profiles
# -----------------------
def make_radial_grid(rmin=1e-18, rmax=1e-12, n=200):
    return np.logspace(np.log10(rmin), np.log10(rmax), n)

def omega_profile(r, vs=VS, rc=RC):
    """Omega(r) = (vs / rc) * exp(-r/rc)"""
    return (vs / rc) * np.exp(-r / rc)

def v_theta_profile(r, omega):
    """v_theta(r) = Omega(r) * r"""
    return omega * r

def dynamic_pressure(rho, v_theta):
    """0.5 * rho * v_theta^2 (Pa = J/m^3)"""
    return 0.5 * rho * (v_theta**2)

def energy_density_prefactor(alpha=ALPHA, phi=PHI):
    """Master prefactor 4/(alpha*phi)"""
    return 4.0 / (alpha * phi)

def energy_density_local(rho, v_theta, alpha=ALPHA, phi=PHI):
    pref = energy_density_prefactor(alpha, phi)
    return pref * 0.5 * rho * (v_theta**2)

def time_dilation_factor(v_theta, c=C):
    """dt_local/dt_inf = sqrt(max(0, 1 - v^2/c^2))"""
    arg = 1.0 - (v_theta**2) / (c**2)
    # numerical safety
    arg = np.maximum(arg, 0.0)
    return np.sqrt(arg)

# -----------------------
# I/O / plotting helpers
# -----------------------
def save_line_plot(x, y, xlabel, ylabel, title, outpath,
                   xscale="log", yscale="log", figsize=(6,4)):
    plt.figure(figsize=figsize)
    if xscale == "log":
        plt.xscale("log")
    if yscale == "log":
        plt.yscale("log")
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, which="both", linestyle=":", linewidth=0.3)
    plt.tight_layout()
    # save multiple formats
    outpath = Path(outpath)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outpath.with_suffix(".png"), dpi=300)
    plt.savefig(outpath.with_suffix(".pdf"))
    plt.savefig(outpath.with_suffix(".svg"))
    plt.close()

# -----------------------
# Main regeneration routine
# -----------------------
def regen_plots(outdir=".", rmin=1e-18, rmax=1e-12, npts=200):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    r = make_radial_grid(rmin, rmax, npts)
    Omega = omega_profile(r)
    v_theta = v_theta_profile(r, Omega)
    p_dyn = dynamic_pressure(RHO_F, v_theta)
    e_local = energy_density_local(RHO_F, v_theta)
    td = time_dilation_factor(v_theta)

    # SAVE plots (same names as I used in the session)
    save_line_plot(r, Omega,
                   xlabel="r (m)",
                   ylabel=r"$\Omega(r)\ \mathrm{(rad\,s^{-1})}$",
                   title="Swirl angular velocity profile — Canon ansatz",
                   outpath=outdir / "omega_profile")
    save_line_plot(r, np.abs(v_theta),
                   xlabel="r (m)",
                   ylabel=r"$v_\theta(r)\ \mathrm{(m\,s^{-1})}$",
                   title=r"Tangential velocity profile $v_\theta(r)=\Omega(r)r$",
                   outpath=outdir / "vtheta_profile")
    save_line_plot(r, p_dyn,
                   xlabel="r (m)",
                   ylabel="Dynamic pressure (Pa)",
                   title=r"Local dynamic pressure $(1/2)\rho_f v_\theta^2$",
                   outpath=outdir / "pressure_profile")
    # time dilation: linear y makes sense for values near 1
    plt.figure(figsize=(6,4))
    plt.xscale("log")
    plt.plot(r, td)
    plt.xlabel("r (m)")
    plt.ylabel(r"$dt_{\rm local}/dt_{\infty}$")
    plt.title("Local time-dilation factor vs radius")
    plt.grid(True, which="both", linestyle=":", linewidth=0.3)
    plt.tight_layout()
    td_out = outdir / "time_dilation_profile"
    plt.savefig(td_out.with_suffix(".png"), dpi=300)
    plt.savefig(td_out.with_suffix(".pdf"))
    plt.savefig(td_out.with_suffix(".svg"))
    plt.close()

    # Save CSV with sample rows (same 12-point sample as session)
    sample_idx = np.linspace(0, len(r)-1, 12, dtype=int)
    df = pd.DataFrame({
        "r_m": r[sample_idx],
        "Omega_rad_s": Omega[sample_idx],
        "v_theta_m_s": v_theta[sample_idx],
        "dynamic_pressure_Pa": p_dyn[sample_idx],
        "energy_density_J_m3": e_local[sample_idx],
        "time_dilation": td[sample_idx]
    })
    csv_path = outdir / "sst_profile_samples.csv"
    df.to_csv(csv_path, index=False)

    # Return paths for convenience
    return {
        "omega": outdir / "omega_profile.png",
        "vtheta": outdir / "vtheta_profile.png",
        "pressure": outdir / "pressure_profile.png",
        "time_dilation": outdir / "time_dilation_profile.png",
        "csv": csv_path
    }

# -----------------------
# CLI
# -----------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate SST canonical plots")
    parser.add_argument("--outdir", default="./figs", help="Output directory")
    parser.add_argument("--rmin", type=float, default=1e-18, help="Min radius (m)")
    parser.add_argument("--rmax", type=float, default=1e-12, help="Max radius (m)")
    parser.add_argument("--npts", type=int, default=200, help="Number of radial points")
    args = parser.parse_args()

    produced = regen_plots(outdir=args.outdir, rmin=args.rmin, rmax=args.rmax, npts=args.npts)
    print("Produced files:")
    for k, p in produced.items():
        print(f"  {k}: {p}")