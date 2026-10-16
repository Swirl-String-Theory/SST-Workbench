# A063 Hicks/Hill T(3,4) finite vortex-tube falsifier v0.2.0

**Independent scientific reference instance, built on the exact model routines of A063 v0.1.1; NOT a canonical frozen framework v1.0.7 instance.** It generates its own LaTeX, plots, `GATE_LEDGER.json`, `RUN_SUMMARY.json`, and PDF. Existing A063 v0.1.1 and other falsifiers are not modified.

## Research question

Can the exact Hicks/Beltrami closed `T(3,4)` vortex field line be thickened to a finite **vorticity-aligned material tube** that remains dynamically stable?

The experiment separates four claims: vortex line; geometric regular neighborhood; stationary material vorticity surface; 3-D nonlinear Euler stability. Different branches can have different results. A failure in one does not terminate the other gates.

## What is actually computed

* Fresh SciPy FP64 trajectory integration over four poloidal cycles; compares full 3D closure and Poincare winding.
* Four generic planar projections of the numerical polygon, over/under crossing extraction using Shapely, and a Wirtinger/Fox Alexander minor via SymPy. Includes a separate analytical trefoil control test.
* Sampled curvature radius, nonlocal point-distance proxy and distance to the Hicks spherical separatrix. These are **not rigorous embedded-tube-reach lower bounds**.
* Normal velocity and vorticity flux of constant-radius normal tubes with three radii; zero-radius control and second sampling resolution.
* Poincare return-map shear on an initial-condition ladder. This is field-line topology, not temporal Euler growth.
* Prescribed-field Lagrangian advection of a knotted material surface (initial 384 points, confirmation 720) over 0, 1, 2 and 4 periods; deformation relative to the original closed core. This is **NOT self-consistent 3D perturbed Euler evolution**.
* Fieldline Beltrami residual, distributed vorticity controls, independent source/protocol SHA-256 ledger, PDF.

## Run on Windows

The commands assume Python 3.11+ and an available LaTeX installation (MiKTeX or TeX Live) for the full PDF. `pdflatex` on PATH is used. No existing SST framework installation is required.

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd FULL
```

`run_all.cmd BASIC` runs a reduced two-projection diagnostic and intentionally leaves the four-projection certification gate `UNRESOLVED`.

On Linux or macOS: `python -m pip install -r requirements.txt && bash run_all.sh FULL`.

Outputs are written to `A063_Hicks_Hill_Torus_Tube_Falsifier_v0.2.0-outputs/`, with scientific report source/PDF in `A063-v0.2.0-reports/`. If TeX is unavailable, LaTeX source and figures remain available; install a PDF backend and rerun `python generate_report.py`.

## Gate semantics

| Gate | Meaning | Expected scope |
|---|---|---|
| T0 | release-side source hashes | not v1.0.7 FREEZE |
| T1 | numerical 3:4 closure | numerical line only |
| T2 | 4-direction Alexander invariants | numerical geometry, no isotopy interval proof |
| T3 | sampled thickness/clearance | *not* certified continuum reach |
| T4 | Beltrami alignment | vortex core line |
| T5 | material boundary of constant-radius tube | failure rejects this particular steady tube |
| T6 | zero shear of co-periodic neighboring lines | failure rejects exact same-period annulus |
| T7 | distributed vorticity control | Hicks vorticity not compactly supported on the knot |
| T8A | prescribed-field surface advection | **PASS means diagnostic ran; not stability** |
| T8 | nonlinear Euler stability | UNRESOLVED without self-consistent PDE run |
| T9 | C++ FP64 / v1.0.7 certification | NOT RUN |
| T10 | existential stable knotted finite tube | UNRESOLVED until stronger tests |

**Scientific interpretation:** A `T(3,4)` vortex-line knot is strongly supported numerically. A naive constant-radius **stationary** vortex tube around it is not invariant. Neighboring lines phase shear. A material tube transported by an exact smooth flow is allowed to deform and can preserve knot topology without remaining spatially localized. No full Euler instability theorem or experimentally validated SST particle claim is made.

## Future self-consistent Euler certification

Require an explicit **finite** volume-vorticity carrier, material boundary tracking, divergence-free 3D perturbations, pressure-Poisson closure, energy/helicity conservation, topology diagnostics, at least three spatial resolutions, three perturbation amplitudes, and sufficient run duration. Use C++ FP64 certification in a separately instantiated canonical framework v1.0.7 successor where available. `BASIC/FULL` here are portable science modes, not framework v1.0.7 commands.

Legacy base: `A063-v0.1.1` Hicks/Hill geometry (`hicks_hill/analytic.py`, `hicks_hill/qualification.py`), with its original source preserved in this package. No changes to earlier frozen releases.
