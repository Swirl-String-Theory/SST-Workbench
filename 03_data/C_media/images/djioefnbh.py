#!/usr/bin/env python3
# Figure 3 — c_T vs c13 with GW170817 bounds
# Produces: sst_constraints_cT_c13.png and sst_constraints_cT_c13.svg

import numpy as np
import matplotlib.pyplot as plt

# -----------------------------
# Config (tweak as needed)
# -----------------------------
GW_EPS = 1.0e-15          # |c_T/c - 1| <= GW_EPS (GW170817 band)
C13_MIN, C13_MAX = -1.0e-2, 1.0e-2  # x-axis range for c13
N = 20001                  # resolution (dense so lines look perfect)
SHOW_LINEAR = True
SHOW_EAETHER = True
SHOW_CUSTOM = True
BETA_CUSTOM = 0.7          # c_T^2 = 1 + beta * c13

TITLE = r"Constraints: $c_T$ vs $c_{13}$ (GW170817 band)"


# -----------------------------
# Theory mappings c13 -> c_T
# -----------------------------
def cT_linearized(c13):
    # Small-coupling toy: c_T^2 = 1 + c13  (=> c_T ≈ 1 + 0.5 c13 for |c13|<<1)
    val = 1.0 + c13
    val[val <= 0] = np.nan
    return np.sqrt(val)

def cT_einstein_aether(c13):
    # Einstein–Æther–like: c_T^2 = 1/(1 - c13)
    # Valid only for c13 < 1; near c13->1 the curve diverges.
    denom = 1.0 - c13
    denom[denom <= 0] = np.nan
    return 1.0/np.sqrt(denom)

def cT_custom(c13, beta=BETA_CUSTOM):
    # Custom model: c_T^2 = 1 + beta * c13
    val = 1.0 + beta*c13
    val[val <= 0] = np.nan
    return np.sqrt(val)


# -----------------------------
# Helper: infer c13 bounds from |c_T-1|<=eps for each mapping
# -----------------------------
def bounds_from_band(mapper, name, eps=GW_EPS):
    # We solve for c13 such that c_T in [1-eps, 1+eps].
    # Use a dense grid and find min/max c13 where curve enters the band.
    c13 = np.linspace(C13_MIN, C13_MAX, N)
    cT = mapper(c13)
    ok = np.isfinite(cT) & (cT >= 1.0 - eps) & (cT <= 1.0 + eps)
    if not np.any(ok):
        print(f"[{name}] No overlap with GW band in plotted range.")
        return None
    c13_ok = c13[ok]
    lo, hi = c13_ok.min(), c13_ok.max()
    print(f"[{name}] c13 allowed (within |c_T-1|≤{eps:g}):  [{lo:.3e}, {hi:.3e}]")
    return lo, hi


# -----------------------------
# Plot
# -----------------------------
def main():
    fig, ax = plt.subplots(figsize=(9, 6), dpi=140)

    # Axes ranges & labels
    ax.set_xlim(C13_MIN, C13_MAX)
    pad = 5*GW_EPS if GW_EPS>0 else 1e-15
    ax.set_ylim(1.0 - 8*pad, 1.0 + 8*pad)
    ax.set_xlabel(r"$c_{13}$", fontsize=12)
    ax.set_ylabel(r"$c_T$", fontsize=12)
    ax.set_title(TITLE, fontsize=13)

    # GW170817 horizontal band
    ax.axhspan(1.0 - GW_EPS, 1.0 + GW_EPS, color="#2ca02c", alpha=0.18,
               label=fr"GW170817: $|c_T/c - 1|\leq {GW_EPS:.0e}$")
    # Center line at c_T=1
    ax.axhline(1.0, color="#2ca02c", lw=1.5, alpha=0.7)

    # Compute theory curves
    c13 = np.linspace(C13_MIN, C13_MAX, N)

    if SHOW_LINEAR:
        y = cT_linearized(c13)
        ax.plot(c13, y, color="#1f77b4", lw=2.0, label=r"Small-coupling: $c_T^2=1+c_{13}$")
        bounds_from_band(cT_linearized, "Linearized", GW_EPS)

    if SHOW_EAETHER:
        y = cT_einstein_aether(c13)
        ax.plot(c13, y, color="#d62728", lw=2.0, label=r"Einstein–Æther: $c_T^2=\frac{1}{1-c_{13}}$")
        bounds_from_band(cT_einstein_aether, "Einstein–Æther", GW_EPS)

    if SHOW_CUSTOM:
        y = cT_custom(c13, BETA_CUSTOM)
        ax.plot(c13, y, color="#9467bd", lw=2.0, label=fr"Custom: $c_T^2=1+{BETA_CUSTOM:g}\,c_{{13}}$")
        bounds_from_band(lambda x: cT_custom(x, BETA_CUSTOM), "Custom", GW_EPS)

    # Cosmetics
    ax.grid(True, ls=":", lw=0.8, alpha=0.6)
    ax.legend(frameon=False, fontsize=10, loc="upper left")

    # Annotation for GW event
    ax.text(0.02, 0.05, "GW170817\n2017-08-17", transform=ax.transAxes,
            color="#2ca02c", fontsize=10, ha="left", va="bottom")

    plt.tight_layout()
    fig.savefig("sst_constraints_cT_c13.png", dpi=250)
    fig.savefig("sst_constraints_cT_c13.svg")
    plt.show()


if __name__ == "__main__":
    main()
