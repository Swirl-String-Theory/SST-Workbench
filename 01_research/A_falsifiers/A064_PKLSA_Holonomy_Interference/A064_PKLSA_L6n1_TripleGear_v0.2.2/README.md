# A064 v0.2.2 — L6n1 / T(3,3) / Triple Gear three-core contrast

A self-contained **research prototype** extending A064 v0.2.1. Input geometry, Python sources, preregistration, NPZ velocity fields, SHA-256 source provenance, numerical Euler diagnostics, discovery seals, tracer audits, TeX, PDF and plots are all present in the ZIP. Offline Python package dependencies must already be installed or installed through the runner.

## Why these three cases?

The Knot Atlas identifies **L6n1 = 6^3_3**, a 3-component Hopf link. The published Schleimer–Segerman Triple Gear is mechanically based on the same isotopy class, with every pair linked. They are **not** Borromean: removing any component leaves a linked pair. The three A064 lanes intentionally compare different **geometric embeddings** of the same link class, unlike v0.2.1 (Borromean L6a4 and its locally knotted 5_2 / 6_1 variants).

| Case | Input | Description |
|---|---|---|
| `L6n1_KNOTPLOT` | Source-native `link_6.3.3.txt` from Google Drive | Three closed polygons split at validated native component jumps; one component orientation inverted to compare fixed signed circulations |
| `T33_KNOTPLOT` | Source-native `torus_3.3.txt` from Google Drive | T(3,3) 3-component torus-link embedding |
| `TRIPLE_GEAR_HOPF_PROXY` | Schleimer–Segerman published three-rotated-circle placement | Centerline model using r=0.4950197 and plane theta=-0.8560281; a mirror matches source chirality |

This v0.2.2 tranche tests the **unadorned three-component skeletons**; it does NOT yet locally insert 5_2/6_1 knots into the Hopf or gear loops. Those cross-combinations should be built and separately topology-qualified in the next matrix campaign to match the v0.2.1 Borromean decorations.

Both native inputs share the **same KnotPlot provider group**, so they are not E011 cross-provider evidence. Exact connected Google Drive IDs and URLs are archived in `data/native/SOURCE_DRIVE_PROVENANCE.json`.

All sources are local. Native component split uses >2.5 times the source median edge length, closure validation, source hashing and local linear resampling. A *collective* similarity fit normalizes maximum absolute bounding-box half-width to 2.35 model units. Three Alexander determinant screens per component return 1; Gauss linking is approximately -1 for all three pairs (after documented orientation alignment). This is a **necessary topology screen**; it is not an isotopy proof or an E011 provider certificate.

**The Triple Gear case models only centerlines, not gear teeth, central helical shaft, mechanical contact forces, torque, ratios, or phase locking.** A real Triple Gear fluid-coupling falsifier requires a separate explicit load/forcing model with independent parameters and controls. The old research note `data/native/TRIPLE_GEAR_NOTE.md` and fitted-lane provenance note are included for context, *not used as numerical source geometry*.

## Launch on Windows

```bat
run_all.cmd SELFTEST
run_all.cmd VALIDATE
run_all.cmd RUN
run_all.cmd BUILD --case L6n1_KNOTPLOT --grid 32
run_all.cmd BUILD --case T33_KNOTPLOT --grid 48
run_all.cmd REPORT
```

`run_all.cmd` defaults to `RUN` (the N=24 campaign). `BUILD --case` regenerates the specified source-derived velocity NPZ and all later audits, but an existing NPZ must have an exact parameter and SHA-256 match or regeneration requires `--force`. Each (case, grid) writes to its own folder. `REPORT` inventories all completed output folders and **never fills missing data with invented values**. Tests: 10/10 PASS on the bundle that was built.

## Scientific method and gates

1. Three separately initialized, genuine time-varying **periodic incompressible 3D Euler** models, 13 saved frames, model duration 0.32, shared Gaussian core radius 0.42 and normalized RMS speed 1.0. Spatial discretization uses 2/3-dealiased Fourier modes and RK4; this is not physical SST unit calibration.
2. The preregistered percentiles 65/75/85/92/96/98/99/99.5 define candidate closed enstrophy surfaces at t=0. The complete discovery JSON and optional mesh receive SHA-256 seals **before** transport code executes.
3. Compare feature-relative normal speed, tracer inside/outside changes, genus-one candidates, and nearest-to-*advected* centerline neighborhood reassignment. All are finite-time candidate-feature observations only.
4. Convergence is **UNRESOLVED** until flux and tracer data stabilize across grids, temporal resolution and core-width. A dynamic separatrix is **UNRESOLVED** until an independent invariant-manifold/material-barrier test is implemented.
5. E011 provider anchors: **NOT MAPPED**; canonical framework v1.0.7 FREEZE/CERTIFY: **NOT EXECUTED**. Explicit CLI commands `FREEZE` and `CERTIFY` refuse certification with nonzero status.

### Grid completion as packaged

All cases have complete N=24 and N=32 data; additionally L6n1 and T(3,3) have N=48 data. Triple Gear proxy N=48 is **NOT_COMPLETED** because computation exceeded available runtime and no result is published. `outputs/RUN_SUMMARY.json` preserves this missing-run gate. All three cases are from the same mathematical link class, but the different embeddings have different curvature, material volumes and finite-time transport rates, and the common core width is *not* an effective-curvature match. Therefore differences cannot be attributed to topology or mechanical gearing alone.

## Scientific references

- [Knot Atlas: L6n1](https://katlas.org/wiki/L6n1), original Knotilus Gauss code `1,6,-5,-3:-4,-1,2,5:-6,4,3,-2`.
- S. Schleimer and H. Segerman, *Triple gear* (2013), [arXiv:1304.6859](https://arxiv.org/abs/1304.6859).
- P. G. Saffman, *Vortex Dynamics* (1992), DOI: 10.1017/CBO9780511624063.
- G. Haller, *Lagrangian Coherent Structures* (2015), DOI: 10.1146/annurev-fluid-010313-141322.
- D. DeTurck et al., *Triple linking numbers, ambiguous Hopf invariants...*, arXiv:0901.1612; for nonzero pairwise linking, Milnor's triple invariant is only defined modulo the gcd of the pairwise linking numbers.

On Linux, invoke the shell runner as `bash run_all.sh SELFTEST` (ZIP extraction may not preserve executable permission).
