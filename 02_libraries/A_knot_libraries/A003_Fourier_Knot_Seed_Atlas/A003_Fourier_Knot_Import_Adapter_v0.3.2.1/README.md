# A003 v0.3.2.1 — G5→G6 Receipt Compatibility Hotfix

This is a **versioned maintenance release** of v0.3.2. Previous A003 versions and their output folders remain unchanged. The v0.3.2 live G5 receipt is valid: its source manifest, GateLedger, all 10 relevant G5 gates, and 32 provider observations were intact, but the inherited G6 `g5_check()` version allowlist stopped at v0.3.1 and falsely classified v0.3.2 as FAIL. The allowlist now explicitly includes **v0.3.2 and v0.3.2.1**. The scientific conditions, expected invariant values, fixed provider version, and hash checks remain unchanged. The finder now also searches for G5 runs in v0.3.2.1 and v0.3.2 output directories.

On Windows, install as a separate directory beside the immutable atlas and previous releases. To **reuse the verified historical G5 receipt** and run just G6 without recomputing G5:

```bat
run_all.cmd G6
```

To run a completely fresh G5 followed by G6, with both outputs in the new v0.3.2.1 output directory:

```bat
run_all.cmd COMPLETE
```

`G6P1` should now read `PASS` for the user's validated v0.3.2 G5 receipt. **G6 itself remains `UNRESOLVED`** (G6P8, G6P9, independent provider families). This hotfix is not an Euler, full-topology, or physics certification. The prior original development validations and results below describe the parent v0.3.2, not new full Windows runs.

---

# A003 v0.3.2 — Continuous Topology Safety & Independent Dynamics Qualification

**Depends on:** frozen A003-v0.1.2 atlas; external Framework v1.0.10, E010 v0.3.1 and C005 v0.6.1; Python environment with NumPy, SciPy, ReportLab, and pyknotid 0.5.3 for the independent Alexander/v3 provider. No package silently updates the canonical E010 source tree or the atlas.

## Run on the Windows SST-Workbench

Place the ZIP adjacent to A003-v0.1.2, never overwrite v0.3.1.

```bat
run_all.cmd
run_all.cmd COMPLETE
```

Only new G6: `run_all.cmd G6`; all 40 topology snapshots with pyknotid: `run_all.cmd G6_FULL`. The G5 output from COMPLETE is consumed using the existing source-hashed G5 receipt; G5 science failure is diagnostic, but provenance/integrity failure aborts. Every invocation writes a *new* run directory.

For other independent KnotPlot/Gilbert geometry sources, supply an explicit manifest with at least two distinct provider/method provenance groups:

```bat
run_g6_dynamic.cmd --independent-carriers C:\workspace\projects\SST-Workbench\your_verified_sources.json
```

Manifest format: see `EXTERNAL_CARRIERS_CONTRACT.example.json`. All carriers must already be independently identified as trefoil T(2,3) or torus T(3,5), workbench-relative three-column XYZ paths, with valid SHA-256, distinct source/independence groups and `source_role=computed_geometry_not_empirical`. Arbitrary filenames are never auto-admitted. Separate provenance groups are **computational** sources, not empirical confirmation. Source family dynamics are a bounded separate diagnostic, not a substitute for the A003 four-level run.

`run_all.cmd G6_SAFETY` is synonymous with the complete new G6 diagnostic. Exit code `3` is expected while G6P8/G6P9 remain unresolved.

## New diagnostic gates and methods

| Gate | What it actually tests | Explicit limit |
| --- | --- | --- |
| G6P14 | At each of 16 RK4 step intervals, compute disjoint true finite 3-D segment distances via exhaustive KD-tree broadphase and a sufficient lower bound `d_min(t_k)-2*max_i ||X_i(t_(k+1))-X_i(t_k)||` | Certifies **piecewise-linear vertex interpolation only**, not exact ODE trajectory |
| G6P15 | DOP853 independent time integrator (rtol=1e-9, atol=1e-11) against RK4 N=150 and 300 at common T=2 | Same existing C005 velocity law, not an independent physical model |
| G6P16 | External independent computed-geometry lineage groups, hashed source XYZ, arclength remapping, source-specific two-mesh trajectories and initial/final diagram clearance | Not a replacement for a full knot invariant or 3D Euler |
| G6P8 | Immutable proposed production source contract and 8-carrier persistent index with original E010 contract hash + strict readback audit | Proposal alone is never PASS or a canonical v0.3.1 release update |
| G6P9 | Explicit audit of missing pressure-Poisson, PDE momentum residual, core/vorticity initial data, boundary conditions, independent PDE solver | No complete Euler calculation is present |

The pre-existing G6P10–G6P13 continue unchanged. G6P14/P15/P16 are added as explicit downstream prerequisites. G6 remains `UNRESOLVED` without a new canonical E010 producer release and a separately qualified continuum Euler solver.

## Outputs

In a unique `A003_Fourier_Knot_Import_Adapter_v0.3.2-outputs/<RUN_ID>`: `G6_DYNAMIC_SUMMARY.json`, `G6_DYNAMIC_DIAGNOSTICS.json`, `G6_DYNAMIC_TRAJECTORIES.npz`, `G6P8_E010_PROPOSED_SOURCE_CONTRACT.json`, `G6P8_E010_CARRIER_INDEX_PROPOSAL.json`, `G6P8_CANONICAL_REGISTRY_PROPOSAL_STATUS.json`, `G6P9_EULER_CLOSURE_AUDIT.json`, `GATE_LEDGER.json`, `PDF_RENDER.json`, and `A003_v0.3.2_DYNAMIC_QUALIFICATION_REPORT.pdf`; optional `G6_EXTERNAL_CARRIER_DIAGNOSTICS.json`.

The full-time RK4 states are held for interval safety analysis; the stable NPZ preserves the five quarter-time snapshots at each mesh, as in v0.3.1. This preserves reasonable output sizes. For each stage an exact finite segment-distance check is performed; the sufficient bound can be inconclusive despite no detected contact.

## Reproducibility & source qualification

The included pinned Framework source hash is `e5756c90a34d482e3dec7e0e9a22a131f7b8968f5de492832963f3063008a055`. The user machine reported `CANONICAL_FROZEN`, while the available historical Drive release info is still `LOCAL_VALIDATED_CANDIDATE`; the framework gate checks the actual local status and does not infer freeze from a filename. Scientific `FAIL` does not hide diagnostic results; corrupt source hashes/ledger do abort.

**Unit-test fixtures are not scientific claims.** Validation includes a bounded test with the genuine external C005 code and original A003 source geometry at N=150. The complete Windows run at N=1200, new external provider families, E010 canonical promotion and physical Euler PDE solve have *not* been performed by this release development environment.
