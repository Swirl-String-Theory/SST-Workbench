import json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

runs = sorted((json.load(open(f)) for f in glob.glob("run_q*.json")), key=lambda r: r["q"])
p = runs[0]["params"]
G, R0, a = p["Gamma"], p["R0"], p["a"]
U0 = runs[0]["U"]
a_eff = runs[0]["a_eff"]

rows = []
for r in runs[1:]:
    q = r["q"]
    rows.append({
        "q": q,
        "dU_meas": U0 - r["U"],
        "dU_A_nom": G * a**2 * q**2 / (12 * np.pi * R0),
        "dU_A_aeff": G * a_eff**2 * q**2 / (12 * np.pi * R0),
        "dU_selfcons": r["Jbar"] / (G * r["Rbar"]),
        "dU_hollow": G * a**2 * q**2 / (4 * np.pi * R0),
        "H0_ratio": r["H0"] / r["H_target"],
    })

q2 = np.array([r["q"] ** 2 for r in rows])
dU = np.array([r["dU_meas"] for r in rows])
k_meas = float(np.sum(q2 * dU) / np.sum(q2**2))
k_nom = G * a**2 / (12 * np.pi * R0)
k_eff = G * a_eff**2 / (12 * np.pi * R0)
k_hol = G * a**2 / (4 * np.pi * R0)
resid = dU - k_meas * q2
scatter = float(np.sqrt(np.mean(resid**2)))

with open("results_table.csv", "w") as f:
    f.write("q,dU_measured,dU_modelA_a_nominal,dU_modelA_a_eff,dU_selfconsistent,dU_hollow,H0_over_Htarget\n")
    for r in rows:
        f.write(f"{r['q']},{r['dU_meas']:.6f},{r['dU_A_nom']:.6f},{r['dU_A_aeff']:.6f},"
                f"{r['dU_selfcons']:.6f},{r['dU_hollow']:.6f},{r['H0_ratio']:.4f}\n")
    f.write(f"\nfit dU = k q^2 (through origin): k_meas={k_meas:.6e}, rms scatter={scatter:.2e}\n")
    f.write(f"k_modelA_nominal={k_nom:.6e} (ratio meas/pred={k_meas/k_nom:.3f})\n")
    f.write(f"k_modelA_a_eff={k_eff:.6e} (ratio {k_meas/k_eff:.3f})\n")
    f.write(f"k_hollow={k_hol:.6e} (ratio {k_meas/k_hol:.3f})\n")

qq = np.linspace(0, 27, 100)
fig, ax = plt.subplots(figsize=(7.2, 5.0))
ax.plot(qq, k_hol * qq, "--", color="crimson", lw=1.6,
        label=r"hollow core:  $\Gamma a^2 q^2/4\pi R_0$   ($C=\rho\Gamma^2a^2/4\pi$)")
ax.plot(qq, k_nom * qq, "-", color="C0", lw=1.8,
        label=r"model A (Rankine):  $\Gamma a^2 q^2/12\pi R_0$   ($C=\rho\Gamma^2a^2/12\pi$)")
ax.plot(qq, k_eff * qq, ":", color="C0", lw=1.4, label=r"model A with $a_{\rm eff}$ (smoothed core)")
ax.plot(q2, [r["dU_selfcons"] for r in rows], "s", ms=6, mfc="none", mec="gray",
        label="self-consistent Saffman target  $J/\\Gamma\\bar R$")
ax.plot(q2, dU, "o", ms=7, color="k", label="measured (axisym. Euler, grid level)")
ax.set_xlabel(r"$q^2$  (twist rate$^2$)")
ax.set_ylabel(r"$\Delta U = U(0) - U(q)$")
ax.set_title(f"Twisted vortex ring: speed deficit vs. twist   "
             f"($\\Gamma$={G}, $R_0$={R0}, a={a}, $\\epsilon$={a/R0})")
ax.legend(fontsize=8.5, loc="upper left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("uq_experiment.png", dpi=160)
print(open("results_table.csv").read())
