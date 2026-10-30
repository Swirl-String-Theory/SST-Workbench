# A075-v0.2.9 — Ruban T(2,3) Seed Fidelity & Stability

**Framework:** byte-pinned SST Falsifier Framework v1.1.0; **catalog:** A075; **status:** DEVELOPMENT_ONLY / PHYSICAL_STABILITY_UNRESOLVED. Parent A075-v0.2.7 remains unmodified.

## New central experimental question

Can the reconstructed, mathematically exact analytic T(2,3) with Ruban (2018) parameters B0=77/500, delta=1/20 and Lambda=7/5+ln(200)/2 retain its shape under (a) the regularized filament model, and (b) the separate 3D incompressible inviscid Euler field as resolution and initial core width are varied? The paper's weak stochastic perturbation was not published. This version does NOT reproduce the specific t=320 trajectory or a known optimum.

## Real implementations

- `experiment/ruban.py`: SHA-pinned 2048-point analytically reconstructed equal-arclength trefoil, 4096-point and uniform-angle references, exact winding/torus validation. Reproducible generator and original paper parameter provenance in `inputs/ruban_t23/`.
- `experiment/ruban_study.py`: a single, source-free periodic 3D Euler field initialized from the exact Ruban seed. It has NO incoming donor, second receiver, or imposed knotted motion. It measures energy, enstrophy and translation-invariant spectral magnitude change. It compares the original analytic B0=0.32 trefoil at exactly the same R0=1, circulation Gamma=2*pi, Gaussian sigma, box, t_end and grid. Optional time and spatial refinement.
- `experiment/ruban_filament.py`: OPTIONAL short finite-difference/midpoint diagnostic of Ruban Eq.(9), including exact delta=0.05 and Lambda_tilde0/2. Not Ruban's pseudospatial discretization or original perturbed data; Hamiltonian and best-fit geometric error are diagnostic only.
- `experiment/backend_matrix.py`: when `--ruban-study` is set, the Framework 2-of-3 scientific backend matrix runs actual SOURCE-FREE RUBAN trajectories on Python, native pybind11 and Intel PyTorch XPU when available. Probes alone are excluded. For ordinary BASIC without the flag, the previous 0_1 donor/control method is retained.
- `experiment/heartbeat.py`: source-free and filament trajectories emit progress telemetry, with `run_all.cmd STATUS` available separately.

## Core parameters ARE NOT interchangeable

Ruban's delta is a filament Biot-Savart regularizer; Euler's `sigma` is a Gaussian spectral smoothing width. For L=10 and n=80, dx=0.125 so r_minor/dx=1.232. A075 sigma=0.5 gives 4 cells/sigma but sigma/r_minor=3.247. Initial fine-scale torus structure is not spatially resolved. Ruban t=320 is dimensionless and not assigned to A075 Euler seconds without a scaling derivation.

## Scientific gates

- G11: geometric fidelity (hash, closed polygon, winding, R0/r0), PASS on verified geometry only.
- G12: source-free Euler longevity/topology/core/domain convergence, UNRESOLVED (even if the short solver runs correctly).
- G13: Eq.(9) diagnostic filament vs paper dynamics and author perturbations, UNRESOLVED.
- G1/G5/G6/G7/G10 and G2/G3/G8 are retained. G2/G3/G8 may not be promoted by a source-free geometric smoke.

## Run on Windows

See `RUBAN_INSTALL_NL.md` for full commands and exact output paths. From the activated `.venv-a075-xpu` environment:

```bat
python -m pytest -q tests
python tools\check_sources.py
python tools\verify_ruban.py
run_all.cmd RUBAN_PREVIEW --grid 24 --grid-up 32 --t-end 0.04 --dt 0.01 --threads 12
run_all.cmd RUBAN_FILAMENT --filament-points 128 --filament-t-end 0.04 --filament-dt 0.005
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --ruban-study --grid 80 --grid-up 112 --threads 12 --allow-expensive --heartbeat-seconds 10
```

`--ruban-refinement` optionally adds dt/2 and finer grid levels; `--ruban-filament` also adds optional Eq.(9) diagnostic to official Ruban studies. Only after a fresh version-specific FREEZE is a Framework output qualifying as frozen generated. A source-free Ruban run has **no donor-exit or energy-retention claim**. Plain `BASIC`/`FULL` remains backward-compatible with the legacy capture tests.

## Nieuw in v0.2.9: Depositie en geometrietracking

Lees `RUBAN_DEPOSITION_PATCH_v0.2.9_NL.md`. Start `run_all.cmd RUBAN_DEPOSITION --deposition-grids 24,32 --deposition-sigmas 0.5 --deposition-boxes 10 --threads 12`. Deze zelfstandige audit produceert geen Framework-gates en geen fysische stabiliteitsclaim.
