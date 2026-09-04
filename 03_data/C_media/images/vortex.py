# Delocalized photon plots for SST (streamplots), one figure per plot.
# Requirements: matplotlib, numpy. Do not set colors (default only).

import numpy as np
import matplotlib.pyplot as plt

# ---------- Domain ----------
N = 400
x = np.linspace(-1.0, 1.0, N)
y = np.linspace(-1.0, 1.0, N)
X, Y = np.meshgrid(x, y)
R = np.hypot(X, Y)

# ---------- 1) Localized vortex core ----------
Gamma = 1.0       # arbitrary visualization circulation
core = 0.05       # core radius (plot units)
vtheta = (Gamma/(2*np.pi)) * (R/(R**2 + core**2))

with np.errstate(divide='ignore', invalid='ignore'):
    Ux = -vtheta * Y / (R + 1e-12)
    Uy =  vtheta * X / (R + 1e-12)
Ux[R < 1e-3] = 0.0
Uy[R < 1e-3] = 0.0

plt.figure(figsize=(6,6))
plt.streamplot(X, Y, Ux, Uy, density=2.0, linewidth=1)
plt.scatter([0],[0], s=40)  # mark core
plt.title("Localized Vortex Core (streamlines)")
plt.xlabel("x (arb. units)")
plt.ylabel("y (arb. units)")
plt.axis("equal")
plt.tight_layout()
plt.savefig("localized_vortex.png", dpi=180)
plt.close()

# ---------- 2) Pulsed swirl waves (three phases) ----------
A0 = 1.0
k = 8*np.pi      # ~4 rings across radius
omega = 6.0      # visualization frequency (arb. units)
alpha = 0.5      # radial damping for clean plot
core_term = (Gamma/(2*np.pi)) * (R/(R**2 + 0.03**2))

def frame(t, fname):
    vth = A0*np.cos(k*R - omega*t)*np.exp(-alpha*R) + 0.25*core_term
    with np.errstate(divide='ignore', invalid='ignore'):
        Ux = -vth * Y / (R + 1e-12)
        Uy =  vth * X / (R + 1e-12)
    Ux[R < 1e-3] = 0.0
    Uy[R < 1e-3] = 0.0

    plt.figure(figsize=(6,6))
    plt.streamplot(X, Y, Ux, Uy, density=2.0, linewidth=1)
    plt.scatter([0],[0], s=40)
    plt.title(f"Pulsed Swirl Waves (t = {t:.2f})")
    plt.xlabel("x (arb. units)")
    plt.ylabel("y (arb. units)")
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(fname, dpi=180)
    plt.close()

times = [0.0, np.pi/omega, 2*np.pi/omega]
for i, t in enumerate(times):
    frame(t, f"pulsed_wave_t{i}.png")

print("Saved:",
      "localized_vortex.png",
      "pulsed_wave_t0.png",
      "pulsed_wave_t1.png",
      "pulsed_wave_t2.png")
