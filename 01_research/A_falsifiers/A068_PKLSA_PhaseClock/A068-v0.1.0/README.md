# SST / PKLSA Intrinsic Phase Clock - v0.1.0 PRE-FLIGHT

**Scope:** Scientific preregistration prototype. This is **not** a new official A-number, nor a blind SST Framework v1.0.7 instance, and it does **not** establish a physically realizable PKLSA clock.

## Run

Windows: `run_all.cmd`  
Linux/macOS: `python -m pytest -q tests && python src/phaseclock.py --a064 data/A064-v0.3.0_results.json`

Run on actual incompressible periodic Euler 3D velocity *snapshots* (not geometry):

`python src/phaseclock.py --field-npz PATH_TO_TIME_SERIES.npz --out outputs/FIELD_PREFLIGHT.json`

Required NPZ keys:
- `t`: strictly increasing equally spaced times; units declared externally (may be dimensionless)
- `u`: shape `(nt,n,n,n,3)` divergence-free Euler velocity; **not** a KnotPlot curve
- `domain_length`: one scalar, same spatial units as `u` grid
- optional `material_mask`: shape `(nt,n,n,n)`; an external flow-derived, topology-qualified material tube mask. Without such a mask, screening uses whole-box enstrophy and cannot certify a local vortex clock.

Fourier curl gives omega; normalized enstrophy-weighted covariance eigenvalue gaps are two rotation- and translation-invariant scalar shape observables. Hilbert phase is extracted from **measured** observables, not defined as a field, and thresholds are screening proposals, not final preregistration. Numerical failure does not falsify every possible physical clock.

## Source status
The included `data/A064-v0.3.0_results.json` is a copy of the user's connected Drive output, read 16 October 2026. A064 v0.3.0 has instantaneous matrix-free Fourier--Galerkin linear Euler eigenpairs of a nonstationary geometry-initialized background. It has no certified Kelvin branch, relative periodic equilibrium, materially bounded vortex, SI scale, or multi-provider physics qualification. Existing A064 wavepacket detector curves are **not** 3D-vortex shape clock trajectories.

## Scientific gates for a production-grade blind implementation
G0 source-provenance and pre-registered 3 independent groups (D1 analytical, D2 dynamic Euler, D3 independent PKLSA); G1 3D Euler conservation and phase-space frame reduction; G2 stable period/relative period without selecting target period; G3 two observable phases/cross checks; G4 independent withheld linear/Floquet frequency prediction; G5 space/time/core/numerical-backend convergence; G6 cross-provider source replication; G7 null controls and Galilean/scaling invariances; G8 post-reveal SST comparison only. **All gates must be tested independently**, even when an earlier gate fails.

## Frozen framework policy
Do not modify `SST_Falsifier_Framework_v1.0.7`. After official A-ID verification, create a separate instance using the `tools/new_falsifier.py` generator from the frozen framework, pin the framework root, run `FREEZE`, `BASIC`, `CERTIFY`, `REVEAL_IF_ALLOWED`. Every unresolved physical gate keeps reveal closed. Do not claim this prototype executed the framework.

## Output policy
This prototype's `outputs/` is a development artifact. A certified instance must follow the official `_BLIND.zip`, `_REVEALED.zip` and parent-folder PDF conventions from the framework.

## Sources
- A064 v0.3.0 [existing report](https://drive.google.com/file/d/1ET-KuARq9_TsgFszuqUflLXPnkW3vGIU/view)
- A064 [existing source](https://drive.google.com/drive/folders/1v5Ty5KIZezA-CtdzCPZhkdc6bx0IrQ7_)
- Frozen [framework v1.0.7](https://drive.google.com/drive/folders/1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE)
