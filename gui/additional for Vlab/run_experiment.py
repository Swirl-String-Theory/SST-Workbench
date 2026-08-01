"""U(q) experiment: twisted-ring propagation speed vs core twist.

Targets (per unit density, Gamma=1):
    a-priori (model A, uniform-twist Rankine):  dU = -Gamma a^2 q^2 / (12 pi R0)
    hollow-core alternative:                    dU = -Gamma a^2 q^2 / (4 pi R0)
    self-consistent (profile-exact, from the evolved fields):
        dU_sc = -J / (Gamma * Rbar),   J = int u_phi^2 dr dz  near the ring
(the last line is the Saffman core-constant term evaluated on the actual w-profile,
 so it absorbs profile relaxation after initialization).
"""
import json, time
import numpy as np
from axisym_solver import AxisymSolver, init_twisted_ring

Gamma, R0, a, z0 = 1.0, 1.0, 0.18, 1.5
import sys
QLIST = [float(x) for x in sys.argv[1:]]
T_END = 3.5
FIT_T0 = 0.7

results = {"params": {"Gamma": Gamma, "R0": R0, "a": a, "Nr": 256, "Nz": 512,
                      "Rmax": 3.5, "Zmax": 7.0, "nu": 5e-5, "T": T_END,
                      "fit_window": [FIT_T0, T_END], "qlist": QLIST}, "runs": []}

for q in QLIST:
    sol = AxisymSolver(Nr=256, Nz=512, Rmax=3.5, Zmax=7.0, nu=5e-5)
    om, w = init_twisted_ring(sol, Gamma=Gamma, R0=R0, z0=z0, a=a, q=q)
    # effective core radius from the vorticity second moment (uniform disc: <s^2> = a^2/2)
    s2 = ((sol.R2 - R0) ** 2 + (sol.z[None, :] - z0) ** 2)
    a_eff = float(np.sqrt(2.0 * np.sum(om * s2) / np.sum(om)))
    H0 = sol.helicity()
    t, umax, nstep = 0.0, 1.6, 0
    ts, Zs, Rs, Js = [], [], [], []
    t0 = time.time()
    while t < T_END:
        dt = 0.4 * min(sol.dr, sol.dz) / max(umax, 1e-6)
        umax = sol.step(dt)
        t += dt
        nstep += 1
        if nstep % 10 == 0:
            R, Z = sol.centroid()
            ts.append(t); Zs.append(Z); Rs.append(R)
            Js.append(sol.swirl_energy_integral(Z, 5 * a))
    ts, Zs, Rs, Js = map(np.array, (ts, Zs, Rs, Js))
    sel = ts >= FIT_T0
    U, _ = np.polyfit(ts[sel], Zs[sel], 1)
    Jbar = float(np.mean(Js[sel])) if q > 0 else 0.0
    Rbar = float(np.mean(Rs[sel]))
    run = {"q": q, "U": float(U), "a_eff": a_eff, "H0": H0,
           "H_target": Gamma**2 * q * R0, "Jbar": Jbar, "Rbar": Rbar,
           "Gamma_end": sol.circulation(),
           "P_rel_drift": sol.impulse() / (np.pi * Gamma * R0**2) - 1.0,
           "wall_s": time.time() - t0, "steps": nstep,
           "ts": ts.tolist(), "Zs": Zs.tolist(), "Rs": Rs.tolist(), "Js": Js.tolist()}
    results["runs"].append(run)
    print(f"q={q:4.2f}  U={U:.5f}  a_eff={a_eff:.4f}  H0={H0:.3f}/{Gamma**2*q*R0:.3f}  "
          f"Jbar={Jbar:.5f}  Rbar={Rbar:.4f}  wall={run['wall_s']:.0f}s", flush=True)

for run in results["runs"]:
    with open(f"run_q{run['q']:.2f}.json", "w") as f:
        json.dump({"params": results["params"], **run}, f)

