#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trefoil_energy.py
=================
Main pipeline: ideal trefoil  →  Biot-Savart self-energy  →  energetic
minimum trefoil closure in the SST vortex-filament framework.

Physics
-------
For a thin, closed vortex filament of circulation Γ in a superfluid-like
substrate of density ρ_f, the Biot-Savart self-energy is:

    E_BS(a) = (ρ_f Γ²) / (4π)  ·  I(K, a)

where I(K, a) = Σ_{i≠j} (dl_i · dl_j) / |r_i - r_j|_reg
is the Rosenhead-regularised self-integral (tube radius a).

Asymptotic expansion (a << R_curvature, a >> Δs):

    I(K, a) ≈ A_K · L · ln(L/a) + B_K · L

Universal slender-body limit: A_K → 1 as a/R_curvature → 0 for any smooth
closed curve. (Not 1/4π — that is the coefficient in the BSL velocity field,
not the energy integral. The energy has A_K = 1 in the limit.)

Writhe of the ideal trefoil
---------------------------
The Gauss self-linking integral gives Wr ≈ ±3.41 for the ropelength-
minimising trefoil (the sign depends on handedness). This is NOT 3: 
the ideal embedding has Wr ≈ 3.41 because the writhe is a geometric
invariant of the embedding, not a topological one.

Energetic minimum — two complementary perspectives
---------------------------------------------------
1. Geometric (ropelength):
   The ropelength-minimising ideal trefoil in ideal.txt has
       ropelength  = L / a = 32.743  (Cantarella, Kusner, Sullivan 2002)
   This is the global minimum of the ropelength functional — the thickest
   tube that closes into a trefoil without self-intersection.
   Equivalently: for fixed tube radius r_c, the minimum-energy closed
   trefoil is the one with shortest arc length L = ropelength × r_c.

2. Variational (with surface/core energy):
   Adding E_core ~ π a² / L  (core kinetic energy / pressure term),
   the total E_total(a) = (ρ_f Γ²/4π) × [I(K,a) + π a²/L] has a minimum
       a* = L √(A_K / 2π)
   In SST, the Compton closure fixes the physical tube radius:
       r_c = v_↺ / ω_C = α ħ / (2 m_e c)  ≈  1.409e-15 m

SST interpretation [CALIBRATED]: if the electron is a trefoil swirl string,
the physical knot length is L_phys = ropelength × r_c ≈ 4.62e-14 m.

Usage
-----
    python3 build.py               # compile C++ kernel first
    python3 trefoil_energy.py      # run full pipeline
    python3 trefoil_energy.py --n 1000 --n-pts 50

Author: Omar Iskandarani (ORCID 0009-0006-1686-3961) / Claude (Anthropic), July 2026.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# ── auto-build C++ kernel ──────────────────────────────────────────────────
import build as _build
_build.build(verbose=True)

import sst_bs_kernel as _bs   # noqa: E402
import ideal_source as _ideal  # noqa: E402

# ── physical constants (CODATA 2018) ───────────────────────────────────────
try:
    import scipy.constants as sc
    _hbar  = sc.hbar
    _m_e   = sc.m_e
    _c     = sc.c
    _alpha = sc.fine_structure
except ImportError:
    _hbar  = 1.054571817e-34
    _m_e   = 9.109383702e-31
    _c     = 2.997924580e8
    _alpha = 7.297352569e-3

# ── SST Compton anchor ─────────────────────────────────────────────────────
_omega_C  = _m_e * _c**2 / _hbar           # rad/s
_v_swirl  = _alpha * _c / 2.0              # m/s
_r_c      = _v_swirl / _omega_C            # m  ≈ 1.409e-15 m
_Gamma_0  = 2.0 * np.pi * _v_swirl * _r_c # m²/s


# ══════════════════════════════════════════════════════════════════════════
# 1. Load and evaluate ideal trefoil
# ══════════════════════════════════════════════════════════════════════════

def load_trefoil(N: int = 600):
    L_norm, D, cos_c, sin_c = _ideal.load_knot("3:1:1")
    pts    = _ideal.eval_curve(cos_c, sin_c, N)
    a_norm = D / 2.0          # = 0.5  (tube radius in ideal.txt units)
    ropelen = L_norm / a_norm # ≈ 32.743
    ds_mean = _ideal.arc_length(pts) / N   # mean segment length
    return pts, L_norm, D, a_norm, ropelen, ds_mean


# ══════════════════════════════════════════════════════════════════════════
# 2. Biot-Savart energy sweep
# ══════════════════════════════════════════════════════════════════════════

def energy_sweep(pts, L_norm, a_min, a_max, n_pts=40):
    a_vals = np.logspace(np.log10(a_min), np.log10(a_max), n_pts)
    I_vals = np.zeros(n_pts)

    print(f"\n[sweep] I(K,a) for {n_pts} values "
          f"a ∈ [{a_min:.4g}, {a_max:.4g}] …")
    t0 = time.perf_counter()

    for k, a in enumerate(a_vals):
        I_vals[k] = _bs.biot_savart_integral(pts, a)
        if (k + 1) % 10 == 0 or k == n_pts - 1:
            print(f"  [{k+1:3d}/{n_pts}]  a={a:.5f}  I={I_vals[k]:.4f}"
                  f"  ({time.perf_counter()-t0:.1f}s)")

    return a_vals, I_vals


# ══════════════════════════════════════════════════════════════════════════
# 3. Asymptotic fit
# ══════════════════════════════════════════════════════════════════════════

def fit_asymptotic(a_vals, I_vals, L, ds_mean):
    """
    Fit I(K, a) = A_K · L · ln(L/a) + B_K · L  in the slender-filament
    regime:  3·Δs  <  a  <  L/20

    A_K → 1 universally in the true slender limit (a/L → 0, a/Δs → ∞).
    Finite-a corrections mean A_K from the fit is typically 1–2 for knots.
    """
    a_lo = max(3.0 * ds_mean, a_vals[0])
    a_hi = min(L / 20.0, a_vals[-1])
    mask = (a_vals >= a_lo) & (a_vals <= a_hi)

    if mask.sum() < 3:
        print(f"  [fit] WARNING: only {mask.sum()} points in [{a_lo:.4f},{a_hi:.4f}]")
        print("        Falling back to full range. Accuracy limited.")
        mask = np.ones(len(a_vals), dtype=bool)

    x = np.log(L / a_vals[mask])
    y = I_vals[mask] / L

    def model(x, A, B):
        return A * x + B

    popt, pcov = curve_fit(model, x, y)
    perr = np.sqrt(np.diag(pcov))
    A_K, B_K = popt
    A_K_err, B_K_err = perr
    n_used = int(mask.sum())
    return A_K, B_K, A_K_err, B_K_err, n_used, a_lo, a_hi


# ══════════════════════════════════════════════════════════════════════════
# 4. Energetic minimum
# ══════════════════════════════════════════════════════════════════════════

def find_variational_minimum(A_K, L, a_norm):
    """
    From E_total(a) = C × [I(K,a) + π a²/L] with asymptotic I,
    the minimum is at a* = L √(A_K / 2π).

    Physical interpretation:
      In SST the core energy ~ π a² / L represents the pressure/surface
      energy of the vortex tube. The balance gives a* as the equilibrium
      tube radius. This is labelled [SPECULATIVE] — the core model is ad hoc.
    """
    a_star  = L * np.sqrt(A_K / (2.0 * np.pi))
    rl_star = L / a_star
    a_star_phys = a_star * _r_c / a_norm
    return {
        "a_star_norm":    a_star,
        "a_star_phys_m":  a_star_phys,
        "ropelen_star":   rl_star,
        "ratio_to_ideal": a_star / a_norm,
    }


# ══════════════════════════════════════════════════════════════════════════
# 5. SST physical values
# ══════════════════════════════════════════════════════════════════════════

def sst_physical(A_K, B_K, L_norm, a_norm):
    ropelen  = L_norm / a_norm
    L_phys   = ropelen * _r_c
    # I at the ropelength-minimum tube radius (a = a_norm = 0.5)
    I_at_rmin = A_K * L_norm * np.log(L_norm / a_norm) + B_K * L_norm
    # ρ_f needed so that E_BS = m_e c²
    E_ref    = _m_e * _c**2
    rho_f_mc2 = E_ref / (_Gamma_0**2 / (4.0 * np.pi)) / I_at_rmin
    return {
        "r_c_m":        _r_c,
        "v_swirl_ms":   _v_swirl,
        "omega_C_rads": _omega_C,
        "Gamma_0_m2s":  _Gamma_0,
        "ropelength":   ropelen,
        "L_phys_m":     L_phys,
        "I_at_rmin":    I_at_rmin,
        "rho_f_to_match_mec2": rho_f_mc2,
    }


# ══════════════════════════════════════════════════════════════════════════
# 6. Report
# ══════════════════════════════════════════════════════════════════════════

def print_report(pts, L_norm, D, a_norm, ropelen, ds_mean,
                 a_vals, I_vals,
                 A_K, B_K, A_K_err, B_K_err, n_fit, a_lo_fit, a_hi_fit,
                 Wr, var_min, sst_phys):
    sep = "=" * 66
    print()
    print(sep)
    print("  SST TREFOIL BIOT-SAVART REPORT")
    print(sep)

    print("\n── 1. Geometry (ideal.txt, Id='3:1:1') ──────────────────────")
    print(f"  Arc length L (norm)       = {L_norm:.6f}")
    print(f"  Tube diameter D           = {D:.6f}")
    print(f"  Tube radius a             = {a_norm:.6f}")
    print(f"  Ropelength L/a            = {ropelen:.6f}  (Cantarella+2002: 32.7433)")
    print(f"  Writhe Wr                 = {Wr:.4f}      (ideal trefoil: ≈ ±3.41)")
    print(f"  N sample points           = {len(pts)}")
    print(f"  Mean segment length Δs    = {ds_mean:.5f}")
    print(f"  Kernel: OpenMP={_bs.openmp}, threads={_bs.n_threads}")

    print("\n── 2. Asymptotic fit  I = A_K·L·ln(L/a) + B_K·L ────────────")
    print(f"  Fit range: a ∈ [{a_lo_fit:.4f}, {a_hi_fit:.4f}]  ({n_fit} points)")
    print(f"  A_K         = {A_K:.5f}  ±  {A_K_err:.2e}")
    print(f"  B_K         = {B_K:.5f}  ±  {B_K_err:.2e}")
    print(f"  Slender limit A_K → 1.0 as a/R_curv → 0 (any smooth closed curve)")
    print(f"  Finite-a: A_K ∈ (1,2) for knots in the accessible range")

    print("\n── 3. Energetic minimum ──────────────────────────────────────")
    print(f"  (a) Ropelength minimum  [DERIVED — geometric]")
    print(f"      Ideal trefoil already achieves the constrained minimum:")
    print(f"      max tube radius for given L ↔ min L for given r_c")
    print(f"      ropelength = L/a = {ropelen:.4f}")
    print(f"  (b) Variational minimum  [SPECULATIVE — core model ad hoc]")
    print(f"      E_core ~ π a²/L  →  a* = L√(A_K/2π)")
    print(f"      a* (norm)     = {var_min['a_star_norm']:.5f}")
    print(f"      a* / a_ideal  = {var_min['ratio_to_ideal']:.4f}  (ideal a = {a_norm})")
    print(f"      ropelength @a* = {var_min['ropelen_star']:.4f}")
    print(f"      a* (phys)     = {var_min['a_star_phys_m']:.4e} m")
    print(f"      a* / r_c      = {var_min['a_star_phys_m']/sst_phys['r_c_m']:.4f}")

    print("\n── 4. SST Compton closure ────────────────────────────────────")
    print(f"  r_c  = αħ/(2m_e c)        = {sst_phys['r_c_m']:.6e} m")
    print(f"  v_↺  = αc/2               = {sst_phys['v_swirl_ms']:.6e} m/s")
    print(f"  ω_C  = m_e c²/ħ           = {sst_phys['omega_C_rads']:.6e} rad/s")
    print(f"  Γ₀   = 2π v_↺ r_c         = {sst_phys['Gamma_0_m2s']:.6e} m²/s")
    print(f"  Ropelength                 = {sst_phys['ropelength']:.6f}")
    print(f"  L_phys = ropelength × r_c  = {sst_phys['L_phys_m']:.4e} m")
    print(f"  I(K, a_ideal) [asymptotic] = {sst_phys['I_at_rmin']:.5f}")
    print(f"  ρ_f s.t. E_BS = m_e c²    = {sst_phys['rho_f_to_match_mec2']:.4e} kg/m³")
    print(f"  [CRITICAL NOTE: ρ_f is NOT independently derived here —")
    print(f"   it is calibrated to reproduce m_e c². This is circular.]")

    print()
    print(sep)
    print("  Epistemic labels (SST CANON_SOURCE_HIERARCHY §3)")
    print(sep)
    print("  [ORTHODOX]    Biot-Savart integral, ropelength, writhe computation")
    print("  [ORTHODOX]    A_K → 1 in slender-body limit (classical fluid mech.)")
    print("  [DERIVED]     Wr ≈ -3.41  (Gauss integral on ideal-trefoil geometry)")
    print("  [DERIVED]     L_phys = ropelength × r_c  (Compton closure applied)")
    print("  [CALIBRATED]  r_c = αħ/(2m_e c)  uses α from QED, m_e from particle data")
    print("  [CALIBRATED]  ρ_f matched to reproduce m_e c²  (not independently fixed)")
    print("  [SPECULATIVE] Variational a* as electron equilibrium radius")
    print("  [SPECULATIVE] Trefoil = electron topology assignment")
    print()


# ══════════════════════════════════════════════════════════════════════════
# 7. Optional matplotlib plot
# ══════════════════════════════════════════════════════════════════════════

def plot_energy(a_vals, I_vals, L_norm, a_norm, A_K, B_K, var_min, outfile=None):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa
    except ImportError:
        print("[plot] matplotlib not available — skipping.")
        return

    fig = plt.figure(figsize=(14, 5))

    # -- left: I(K,a) vs a -------------------------------------------------
    ax1 = fig.add_subplot(1, 3, 1)
    mask_pos = I_vals > 0
    ax1.loglog(a_vals[mask_pos], I_vals[mask_pos], "b-o", ms=4, lw=1.5,
               label=r"$I(K,a)$ — C++ kernel")

    a_fit = np.logspace(np.log10(a_vals[0]), np.log10(a_vals[-1]), 300)
    I_fit = A_K * L_norm * np.log(L_norm / a_fit) + B_K * L_norm
    ok = I_fit > 0
    ax1.loglog(a_fit[ok], I_fit[ok], "r--", lw=1.5, alpha=0.7,
               label=rf"fit $A_K={A_K:.3f}$")

    ax1.axvline(a_norm, color="green", ls=":", lw=2, label=f"ropelength min $a={a_norm}$")
    if var_min["a_star_norm"] > 0:
        ax1.axvline(var_min["a_star_norm"], color="orange", ls="-.", lw=2,
                    label=rf"variational $a^*={var_min['a_star_norm']:.3f}$")

    ax1.set_xlabel("Tube radius $a$ (ideal.txt units)")
    ax1.set_ylabel(r"$I(K,a)$")
    ax1.set_title("BS self-integral — ideal trefoil 3:1:1")
    ax1.legend(fontsize=7)
    ax1.grid(True, which="both", alpha=0.3)

    # -- middle: A_K diagnostic plot (I/L vs ln(L/a)) ---------------------
    ax2 = fig.add_subplot(1, 3, 2)
    lnLa = np.log(L_norm / a_vals[mask_pos])
    ax2.plot(lnLa, I_vals[mask_pos] / L_norm, "b-o", ms=4, label=r"$I/(L)$")
    ax2.axhline(1.0, color="gray", ls=":", lw=1.5, label=r"$A_K=1$ (slender limit)")
    # fit line
    x_line = np.linspace(lnLa.min(), lnLa.max(), 100)
    ax2.plot(x_line, A_K * x_line + B_K, "r--", lw=1.5,
             label=rf"$A_K={A_K:.3f}, B_K={B_K:.3f}$")
    ax2.set_xlabel(r"$\ln(L/a)$")
    ax2.set_ylabel(r"$I(K,a)/L$")
    ax2.set_title("Asymptotic fit diagnostic")
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)

    # -- right: 3D knot ---------------------------------------------------
    ax3 = fig.add_subplot(1, 3, 3, projection="3d")
    L_, D_, cc, sc = _ideal.load_knot("3:1:1")
    pts400 = _ideal.eval_curve(cc, sc, N=500)
    ptsC = np.vstack([pts400, pts400[0]])
    ax3.plot(ptsC[:, 0], ptsC[:, 1], ptsC[:, 2], "b-", lw=1.0, alpha=0.8)
    ax3.set_title(f"Ideal trefoil 3:1:1\nL={L_norm:.4f}, Wr≈-3.41")
    ax3.set_xlabel("x"); ax3.set_ylabel("y"); ax3.set_zlabel("z")

    plt.tight_layout()
    out = outfile or (HERE / "trefoil_energy.png")
    plt.savefig(out, dpi=150)
    print(f"\n[plot] saved → {out}")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════
# main
# ══════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description="SST trefoil Biot-Savart energy")
    ap.add_argument("--n",       type=int,   default=600,  help="polygon points")
    ap.add_argument("--a-min",   type=float, default=0.05, help="min tube radius (norm)")
    ap.add_argument("--a-max",   type=float, default=1.5,  help="max tube radius (norm)")
    ap.add_argument("--n-pts",   type=int,   default=40,   help="number of a values")
    ap.add_argument("--no-plot", action="store_true",      help="skip matplotlib")
    ap.add_argument("--plot-out",type=str,   default=None, help="PNG output path")
    args = ap.parse_args()

    print("\n[1/5] Loading ideal trefoil …")
    pts, L_norm, D, a_norm, ropelen, ds_mean = load_trefoil(N=args.n)
    print(f"      L={L_norm:.6f}, D={D}, a={a_norm}, ropelength={ropelen:.6f}, Δs={ds_mean:.5f}")

    print("\n[2/5] Writhe (C++ kernel) …")
    t0 = time.perf_counter()
    Wr = _bs.writhe(pts)
    print(f"      Wr = {Wr:.5f}   (ideal trefoil ≈ ±3.41,  took {time.perf_counter()-t0:.2f}s)")

    a_vals, I_vals = energy_sweep(pts, L_norm, args.a_min, args.a_max, args.n_pts)

    print("\n[4/5] Fitting …")
    A_K, B_K, A_K_err, B_K_err, n_fit, a_lo, a_hi = fit_asymptotic(
        a_vals, I_vals, L_norm, ds_mean)
    print(f"      A_K = {A_K:.5f} ± {A_K_err:.2e},  B_K = {B_K:.5f} ± {B_K_err:.2e}")
    print(f"      fit range: [{a_lo:.4f}, {a_hi:.4f}]  ({n_fit} pts)")

    print("\n[5/5] Energetic minimum + SST physical values …")
    var_min  = find_variational_minimum(A_K, L_norm, a_norm)
    sst_phys = sst_physical(A_K, B_K, L_norm, a_norm)

    print_report(pts, L_norm, D, a_norm, ropelen, ds_mean,
                 a_vals, I_vals,
                 A_K, B_K, A_K_err, B_K_err, n_fit, a_lo, a_hi,
                 Wr, var_min, sst_phys)

    if not args.no_plot:
        plot_energy(a_vals, I_vals, L_norm, a_norm, A_K, B_K, var_min,
                    outfile=args.plot_out)


if __name__ == "__main__":
    main()
