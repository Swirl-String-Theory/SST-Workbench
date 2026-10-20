# A070 (PROVISIONAL) v0.2.1 - STRICT SYNTHETIC BLIND PATCH

2026-10-18 | DEVELOPMENT / NOT CERTIFIED / NO NATIVE PKLSA DATA

**Motivation.** v0.2.0 used an arbitrary 50-degree illustrative angle and fixed Omega=v_swirl/r_c before analyzing the reference mode. Its reported SI group velocity was therefore a reference-scale output, not an independent photon speed. This version pre-registers all angles and k-scales, and runs its BLIND classification only in dimensionless units. No canonical SST speed, core radius, c or desired frequency is used by the blind engine.

## Three different meanings of blind

1. **Masked synthetic controls (implemented):** filenames are random IDs, generator, parameters and ground-truth labels are exclusively in an independent REVEAL archive. The code classifies unlabeled complex time series and freezes a signed digest of its result. This checks mechanism-identification workflow only.
2. **Parameter blindness (implemented):** no SST canonical constants, c, or fitted-to-c conversion in BLIND analysis.
3. **Independent PKLSA / observational blindness (NOT implemented):** source-native 3D PKLSA velocity / vorticity / pressure fields, true independent providers, provenance, qualified 3D convergence, held-out empirical data remain unavailable. No physical certification is warranted.

## Execute

Python 3 with numpy installed. From project root:

```bat
run_all.cmd SELFTEST
run_all.cmd BLIND
run_all.cmd VERIFY
```

On Linux/macOS: `python run_all.py SELFTEST && python run_all.py BLIND && python run_all.py VERIFY`.

The BLIND run reproduces the frozen result; it DOES NOT read the reveal archive. `VERIFY` checks that the frozen lock matches the current blinded inputs and classification. The separate REVEAL zip includes `evaluate.py`, generator and truth. Only open after blind results are frozen. No labels or generating equations tied to particular masked IDs are shipped in the BLIND archive.

## Pre-registered scan

Angles between k and background rotation axis: **0, 15, 30, 45, 60, 75, 90 degrees**. k ratios: **0.25, 0.5, 1, 2, 4**. Endpoint theta=90 is a degeneracy check and is not used to assert positive propagating frequency; theta=0 has zero inertial-wave group speed. No optimizing over theta. No SST constants used in inference.

## Interpretation

The only implemented controls are mathematical synthetic stationary, passive-advection, inertial-wave and externally specified wave-like examples, plus possible mixtures. Even a correctly recovered wave-like synthetic family is NOT evidence for a physical torsional photon. The physical hypotheses H1 finite-core torsional eigenmode, H2 independent Swirl-Clock/rod closure, H3 redshift, light bending and cosmic expansion remain UNRESOLVED / NOT RUN.

The 0.2.0 archive remains unchanged; the new patch is additional and does not imply certified v1.0.7 instance. Full blind version history is in `docs/AUDIT.md`.
