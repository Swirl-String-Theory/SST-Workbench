#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST — Swirl torus with counter-chiral windings, rc callouts, and inset v(r).
Outputs: sst_swirl_torus.png, sst_swirl_torus.svg
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers 3D)
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import Circle

# -----------------------------
# Canon-style constants (editable)
# -----------------------------
rho_f = 7.00000e-7          # kg m^-3 (Canon baseline)
alpha = 7.29735e-3          # fine-structure (Canon identification)
phi = (1 + 5**0.5) / 2      # golden ratio
v_core = 1.09384563e6       # m/s (||v⟲⟲⟲||)
r_c = 1.40897017e-15        # m (string core radius)

# Text (change to match paper notation if needed)
formula_1 = r"$u(r)=\frac{1}{2}\,\rho_f\,v_\theta^2(r)$"
formula_2 = r"$E=\dfrac{4}{\alpha\,\varphi}\,\langle u \rangle$"

# -----------------------------
# Torus surface (core)
# -----------------------------
def torus_surface(R=3.5, r=1.2, nu=180, nv=60):
    """
    Return (X,Y,Z) arrays for a torus of major radius R and minor radius r.
    nu: samples around major circle, nv: around tube.
    """
    u = np.linspace(0, 2*np.pi, nu)
    v = np.linspace(0, 2*np.pi, nv)
    U, V = np.meshgrid(u, v, indexing="ij")
    X = (R + r*np.cos(V)) * np.cos(U)
    Y = (R + r*np.cos(V)) * np.sin(U)
    Z =  r*np.sin(V)
    return X, Y, Z, U, V

# -----------------------------
# Torus-knot windings (helical filaments on the torus)
# -----------------------------
def torus_knot(p=3, q=10, R=3.5, r=1.22, N=2500):
    """
    Parametric centerline for a (p,q) torus knot living on torus (R,r).
    """
    t = np.linspace(0, 2*np.pi, N)
    x = (R + r*np.cos(q*t)) * np.cos(p*t)
    y = (R + r*np.cos(q*t)) * np.sin(p*t)
    z =  r*np.sin(q*t)
    return x, y, z

# -----------------------------
# Stylized swirl velocity profile (for inset)
# Smooth, dimensionless, with v(rc) = v_core and monotone decay for r>rc
# -----------------------------
def v_theta_profile(r):
    # Shape-preserving profile normalized at r=rc
    # vθ(r) = v_core * (r/rc) * exp(1 - r/rc)
    s = np.asarray(r) / r_c
    return v_core * s * np.exp(1 - s)

# -----------------------------
# Plot
# -----------------------------
def main():
    # Figure aesthetics
    mpl.rcParams.update({
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "mathtext.fontset": "stix",
        "figure.dpi": 140
    })

    fig = plt.figure(figsize=(12.5, 8.0))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0f0f0f")  # darker canvas
    fig.patch.set_facecolor("#0f0f0f")

    # --- Torus core ---
    R, r = 3.6, 1.25
    X, Y, Z, U, V = torus_surface(R=R, r=r, nu=200, nv=80)

    # Shaded metallic look via angle-based colormap
    # Use cosine of tube angle V for stripes
    shade = 0.55 + 0.45 * (0.5 + 0.5*np.cos(4*V))
    base_color = np.array([0.80, 0.82, 0.85])  # light gray
    facecols = np.clip(shade[..., None] * base_color, 0, 1)

    ax.plot_surface(
        X, Y, Z,
        facecolors=facecols,
        rstride=1, cstride=1,
        linewidth=0, antialiased=False, shade=False, alpha=0.95
    )

    # --- Counter-chiral windings (blue/orange) ---
    for (p, q, col) in [(3, 10, "#10A6D0"), (3, -10, "#FF8C1A")]:
        xw, yw, zw = torus_knot(p=p, q=q, R=R, r=r*0.97, N=4000)
        ax.plot3D(xw, yw, zw, color=col, linewidth=4.0, solid_capstyle="round")

    # --- Camera & axes ---
    ax.view_init(elev=22, azim=40)
    rng = R + r + 0.6
    ax.set_xlim(-rng, rng)
    ax.set_ylim(-rng, rng)
    ax.set_zlim(-r*1.25, r*1.25)
    for spine in [ax.xaxis, ax.yaxis, ax.zaxis]:
        spine.set_pane_color((0,0,0,0))  # transparent panes
    ax.set_xticks([]), ax.set_yticks([]), ax.set_zticks([])
    ax.set_xlabel(""), ax.set_ylabel(""), ax.set_zlabel("")

    # --- Inset: v(r) profile ---
    ax_in = inset_axes(ax, width="23%", height="23%", loc="lower left",
                       bbox_to_anchor=(0.03, 0.05, 0.5, 0.5),
                       bbox_transform=ax.transAxes, borderpad=0.8)
    r_plot = np.linspace(0.2*r_c, 8*r_c, 350)
    v_plot = v_theta_profile(r_plot)
    ax_in.plot(r_plot/r_c, v_plot/v_core, color="#10A6D0", lw=2.5)
    ax_in.axvline(1.0, color="#999", ls="--", lw=1.0)
    ax_in.set_xlim(0, 8)
    ax_in.set_ylim(0, 1.1)
    ax_in.set_xlabel(r"$r/r_c$", color="w")
    ax_in.set_ylabel(r"$v_\theta(r)/v_\mathrm{core}$", color="w")
    ax_in.tick_params(colors="w")
    [s.set_color("w") for s in ax_in.spines.values()]
    ax_in.set_facecolor("#111")

    # --- rc callout bubble (schematic cross-section) ---
    ax_b = inset_axes(ax, width="17%", height="17%", loc="lower right",
                      bbox_to_anchor=(0.0, 0.02, 0.98, 0.98),
                      bbox_transform=ax.transAxes, borderpad=0.6)
    ax_b.set_aspect("equal")
    ax_b.set_facecolor("#1a1a1a")
    [s.set_color("w") for s in ax_b.spines.values()]
    circ = Circle((0.5, 0.5), 0.42, facecolor="#9aa1a9", edgecolor="black", lw=1.2)
    ax_b.add_patch(circ)
    ax_b.annotate(r"$r_c$", xy=(0.5, 0.5), xytext=(0.86, 0.16),
                  color="w",
                  arrowprops=dict(arrowstyle="->", color="w", lw=1.3))
    ax_b.set_xticks([]); ax_b.set_yticks([])

    # --- Large rc arc + label over the main axes (2D screen coords) ---
    # Purely decorative to echo the sample image
    ax.text2D(0.16, 0.88, r"$r_c$", transform=ax.transAxes, color="w", fontsize=18)
    ax.annotate("", xy=(0.08, 0.84), xytext=(0.30, 0.84), xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="w", lw=1.4, shrinkA=0, shrinkB=0))
    ax.annotate("", xy=(0.92, 0.16), xytext=(0.80, 0.28), xycoords="axes fraction",
                textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="w", lw=1.4, shrinkA=0, shrinkB=0))

    # --- Equations (top-right) ---
    ax.text2D(0.73, 0.84, formula_1, transform=ax.transAxes, color="w", fontsize=16)
    ax.text2D(0.76, 0.76, formula_2, transform=ax.transAxes, color="w", fontsize=16)

    # --- Soft vignette behind the 3D plot (nice paper feel) ---
    # Use a rectangle image overlay with alpha gradient
    from matplotlib.patches import Rectangle
    vignette = Rectangle((0,0), 1, 1, transform=fig.transFigure, zorder=-1,
                         facecolor="#0b0b0b", alpha=1.0)
    fig.patches.append(vignette)

    # Finalize
    plt.tight_layout()
    fig.savefig("sst_swirl_torus.png", dpi=300, facecolor=fig.get_facecolor())
    fig.savefig("sst_swirl_torus.svg", facecolor=fig.get_facecolor())
    plt.show()


if __name__ == "__main__":
    main()
