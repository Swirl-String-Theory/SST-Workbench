# SST Topology - Projection - Phase blind falsifier v0.2.0

**Scientific status:** Synthetic topology validation + real PKLSA static-knot import + exploratory periodic Euler pilot. **NOT** physically certified SST/particle or non-ideal vortex reconnection.

## Setup and Windows execution

```bat
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd CERTIFY
run_all.cmd PKLSA_IMPORT --pklsa external_pklsa\reference\PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz
run_all.cmd PKLSA_IMPORT --pklsa external_pklsa\reference\PKLSA_3_1_CANDIDATE_SURFACE.npz
run_all.cmd EULER_PILOT --pklsa external_pklsa\reference\PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz --grid 24 --steps 8 --duration-model 0.10 --sigma-model 0.50
run_all.cmd PKLSA_DYNAMIC --pklsa C:\work\real_pklsa_trajectory.npz --metadata C:\work\source.json
```

`CERTIFY` intentionally fails closed until external native v1.0.7 backend and actual qualified physical data are available; FAIL gates never halt unrelated diagnostic steps. PDF is automatically written by `FREEZE` and copied to the parent.

## Method summary

G00-G08 preserve v0.1 blinded synthetic controls. G09 performs orientation-aware Gauss linking and Alexander determinants at -1 (not complete knot identities). G10 separately tracks circulation **per material line**, G11 checks the vorticity Euler PDE only with independently supplied velocity grids, G12 requires a solved nonideal mechanism, G13 checks same-final-time numerical refinement, G14 independent-source provenance, G15 unit calibration.

Euler pilot: dimensionless periodic 3D Euler `d u / d t = P(u x curl u)`; 2/3 spectral de-aliasing, RK4, Fourier divergence projection, trilinear material trajectory advection. Initial field = Gaussian-smoothed tangent vorticity from real N300 knot; it is a **model** initial condition and not calibrated to the canonical SST core. Knotted vortex filaments at very short time do not demonstrate particle stability.

## Blind procedure

1. Preserve `datasets/INPUT_MANIFEST.json` and the three `DSxx.truth.aesgcm` files; no truth labels in this ZIP.
2. Freeze outputs. `FREEZE_LEDGER.json` binds files and protocol via SHA-256.
3. Keep existing v0.1 keys outside the package. If ultimately necessary, `REVEAL --keys <path_to_REVEAL_KEYS.json>` verifies v0.1 commitments; it does not magically qualify Euler.
4. A new source release requires a new protocol ID and new pre-registration. The three synthetic datasets are **not a new independent replication** merely because the science module was upgraded.

## PKLSA provenance and limitations

See `external_pklsa/reference/PROVENANCE.json` for byte-identical original KnotPlot N300, and the separate real `CANDIDATE_SURFACE.npz` triangular mesh. Do not connect mesh vertices in raw array order and call the result a knot.

## Native framework v1.0.7

Authoritative frozen framework: https://drive.google.com/drive/folders/1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE . This standalone science module runs independently and must be adapted into a **new instance created by the real framework generator** to claim native C++ FP64 and reveal-integrity certification. Nothing here silently falls back from native to Python.

## Outputs

`../SST_TopologyProjectionPhase_v0.2.0-outputs/` (including generated PDF and JSON), blind ZIP adjacent; `../SST_TopologyProjectionPhase_v0.2.0-exploratory_euler/` contains *separate* dimensionless Euler pilot time series/diagnostics.
