# A064 v0.2.0 — Euler-Evolved PKLSA Separatrix Candidate & Transport Falsifier

**Scientific status:** independent numerical prototype. NOT frozen or certified under SST Falsifier Framework v1.0.7. NOT E011 DYNAMICS_READY. No independent measurement. No claim of an actual dynamical separatrix.

## What changes relative to v0.1.1

Previously, three physically uncalibrated geometries generated *frozen* regularized Biot–Savart model velocity snapshots. v0.2.0 preserves these as historical negative controls under `data/MODEL_NPZ` and adds **genuinely time-evolved** vorticity-induced 3-D velocity snapshots under `data/EVOLVED_NPZ` using a periodic incompressible Euler pseudospectral solver (rotational form, Leray projection, strict 2/3 dealiasing, RK4 integration).

**Initialization:** native KnotPlot / PKLSA raw source centerlines `3_1`, `5_2`, `6_1`. A Gaussian tube of core width `a=0.58` dimensionless units is generated on a periodic cube of side `2π`, and the velocity is projected to divergence-free form. Raw source IDs are not mapped to E011 `STATIC_READY` anchors. Provider independence is not established.

**Units:** `x,y,z,t,v` use an *explicitly artificial* `L0=1 m, T0=1 s, U0=1 m/s` numeric convention to satisfy the legacy snapshot API. They must be interpreted as nondimensional model data. This is **NOT** an SST calibration to `r_c` or characteristic swirl speed.

## Windows execution

1. Extract ZIP with the root folder preserved.
2. `run_all.cmd SELFTEST` — 17 regression tests (no external physics qualification).
3. `run_all.cmd` — verify bundled NPZ files and analyse them, then generate vortex-stretching screen, two-grid screen and PDF report.
4. `run_all.cmd EULER_BUILD --force` — rebuild three NPZs from bundled XYZ geometry.
5. `run_all.cmd EULER_RUN --knot 3_1` — one topology, followed by PDF report for results present.
6. `run_all.cmd EULER_VALIDATE` — validate SHA-256 and numerical model metadata.

Run from the package root; first run creates a Python `.venv` and installs `requirements.txt` from available pip source. Only Python libraries, not project datasets, require installation.

Linux: `python -m euler_extension.cli EULER_RUN` followed by `python -m euler_extension.stretchaudit`, `python -m euler_extension.resolution_screen`, `python -m euler_extension.report` (or `bash run_all.sh`).

`run_all.cmd CERTIFY` / `FREEZE` **fails closed** because official framework integration has not occurred. The original A064 v0.1.1 DEMO / SNAPSHOTS / BUNDLED commands remain accessible for reproduction, but are not v0.2.0 scientific evidence.

## Existing package data

`data/PKLSA_RAW_NATIVE_UNQUALIFIED/` (three original XYZ files)

`data/MODEL_NPZ/` (legacy stationary model NPZs and hashed sidecars)

`data/EVOLVED_NPZ/` (three evolved models, 13 frames × 24 × 24 × 24 × 3, and hashed sidecars)

`data/E011_CONTEXT/` (frozen context-only JSON copies, **NOT** verification of matching upstream provider anchors)

`A064-v0.2.0-outputs/` (phase-D candidate meshes, discovery seals, phase-T tracer and flux results, Euler diagnostic gates, stretching identity and two-grid screening)

`reports/FALSIFIER_REPORT.tex`, `reports/FALSIFIER_REPORT.pdf`, `../A064-v0.2.0_FALSIFIER_REPORT runall.pdf` (generated automatically where TeX available; ReportLab fallback).

## Scientific reading of results

This source code models 3D Euler dynamics and tests whether the specific **enstrophy isosurfaces selected at t=0** are material under those dynamics. Permeability here **does not** prove a vortex tube is porous or that no invariant separatrix exists. An enstrophy level set is generally altered by vortex stretching even for ideal material vortex dynamics:

`D_t |omega|^2 = 2 omega_i omega_j ∂_j u_i`.

CFL/divergence/energy/helicity quality gates and an exploratory vortex-stretching identity audit are recorded. The `6_1` snapshot stretching identity has comparatively high numerical residual. Do not substitute source/model integrity for accuracy/convergence or for independent physical confirmation.

## Unresolved certification and science gates

- E010/E011 provider-anchor mapping and frozen source hash verification on the user's live Workbench.
- Independent provider cohorts and sensitivity to E011 source envelope, especially `6_1`.
- Grid, time-step, core-width and tracer integration convergence across an adequately resolved ladder.
- Material surface comparison based on an advected surface mesh; stable/unstable manifold or finite-time LCS extraction.
- Periodic vs free-space boundary condition sensitivity.
- Integration with frozen Framework v1.0.7 by generating an official *new instance*, without claiming this prototype already has valid framework ledger/commitments.

## Existing references

Helmholtz (1858), Saffman (1992), Hou & Li (2007), Haller (2015). Complete BibItem entries are in `reports/FALSIFIER_REPORT.tex`.