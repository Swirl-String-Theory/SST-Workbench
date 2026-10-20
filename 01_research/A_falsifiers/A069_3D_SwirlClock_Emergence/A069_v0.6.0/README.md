# A069 v0.6.0 — Three-dimensional vortex-line tracking (DEVELOPMENT ONLY)

**Status:** `DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED`. This is an independently runnable diagnostic tranche, **not** an official framework v1.0.9 FREEZE/BASIC instance. The existing v0.5.0 source and BLIND evidence are preserved byte-for-byte. There are **no independent knot eigenmodes or Swirl Clock claims** in this release.

## Scientific aim

Reconstruct the discrete vortex-line graph from a genuine 3D complex Gross–Pitaevskii field, using integer 2π winding of gauge-invariant nearest-neighbor phases on oriented cubic plaquettes. Track basic graph complexity (simple oriented cycles, junctions, components, periodic homology) before claiming knot topology or physical reconnection. A connected polygonal graph is not automatically a trefoil, and changes in plaquette counts are not evidence of reconnection.

## Installation and run

```bat
python -m pip install numpy scipy numba pytest
python -m pytest -q tests
python run_v060_tracking.py --v05-instance "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069-v0.5.0" --kind A --n 32 --segments 96 --steps 8 --dt 0.006 --output results\A_N32.json
python run_v060_tracking.py --v05-instance "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069-v0.5.0" --kind B --mirror --n 32 --segments 96 --steps 8 --dt 0.006 --output results\B_mirror_N32.json
```

Without `--v05-instance`, the script executes a **synthetic straight-vortex reference** (not a trefoil).

The supplied experimental CLI reads v0.5.0 modules and never edits its source, prior outputs, FROZEN_PROTOCOL, blind commitments, or output manifests. The user must install the original v0.5.0 package separately. The v0.5.0 PUBLIC-source ZIP has SHA-256 `bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e`.

## Local evidence (not blind physical evidence)

The nine new unit/regression controls PASS. Four short 3D GP preflights were executed using source geometry A (N=24, 32, 48) and B (N=32) with `dt=0.006`, `steps=8` (T=0.048):

| Seed | Grid | Initial graph (components/defects) | Final graph (components/defects) |
| --- | --- | --- | --- |
| A | 24³ | 1 / 3 | 1 / 0 |
| A | 32³ | 1 / 0 | 1 / 2 |
| A | 48³ | 1 / 0 | 2 / 0 |
| B | 32³ | 1 / 0 | 1 / 0 |

Disagreement in A's graph structure at different grids is a **failed qualification gate**, not proof of physical reconnection or of the underlying continuum vortex geometry. A graph with one simple closed lattice cycle has not had its trefoil knot invariant independently verified. These preflights do not demonstrate long-time stability, frequency locking, relative periodic orbit, or a physical Swirl Clock.

## Proposed physical gates (all NOT QUALIFIED)

- `G25`: convergence of vortex-plaquette graph and extracted subcell centerline (not passed on GP A).
- `G26`: robust knot-type identification (invariants + self-contact and grid refinement); not executed.
- `G27`: time-resolved trajectory matching, contact/reconnection classification against two integrators and dx/dt refinement; not executed.
- `G28`: relative equilibrium / relative periodic orbit after eliminating translation, rotation, gauge phase, remeshing modes; not executed.
- `G29`: independent spectral and reduced Floquet eigenmode prediction on dynamical holdouts; not executed.
- `G30`: independent PKLSA provider physics and A061 clock transfer; not executed.

These are **new proposals**, not recorded PASS, FAIL or official v1.0.9 gate results. Reconnection must be distinguished from graph lattice aliasing; GP reconnections are not automatically permitted as ideal Euler vortex dynamics.

## References and scope

The v0.5.0 3D GP module is licensed/owned by the same project and is consumed read-only. The two 2015 parametric seeds are geometry-only; no legacy KnotPlot relaxation is used. The GP bulk Bogoliubov reference frequency is a numerical solver validation, not a knot mode. See SST_CANON-v0.8.36 Appendix P (RPO/Floquet); §3.14 (conditional Chronos-Kelvin); and Appendix M.2 (reconnection warning).
