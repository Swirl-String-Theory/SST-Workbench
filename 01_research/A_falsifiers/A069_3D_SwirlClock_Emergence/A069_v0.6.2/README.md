# A069 v0.6.2 — Dual-Trefoil 160^3 GP & High-Resolution Tracking

**DEVELOPMENT_NOT_FROZEN_NOT_CERTIFIED**. This package adds new campaigns without mutating v0.5.0 or v0.6.1 source/evidence. No nontrivial trefoil eigenfrequency has been inferred. Code is a development runner, **not the official v1.0.9 framework instance**.

## Scope and naming

- **A** = the original **Fourier A (2015 p.32)** trefoil, *not* a torus-parametric formula.
- **B** = the original **Torus B (2015 p.66)** trefoil.
- Both have **160^3** executable cases. B160 (xi=0.28) meets the preregistered *geometry-screening* conditions; **A160 cannot satisfy all G32 conditions for any xi** at fixed box=10 and historical geometry. For A160, xi=0.08 is a transparent **diagnostic-only** choice.
- Higher-resolution cases B192, B256, additional B192/B256 xi=0.24 core-scale controls, A320 (still diagnostic), and A512 (resource-intensive, first selected A grid meeting the three G32 screening thresholds). **These are not run by default here**, and screening is **not** dynamical qualification.
- **No golden ratio, mass, Compton, Lorentz, clock or delay fit.** Classic incompressible Euler and compressible single-component GP must not be equated.
- **Important GP physical-core consistency repair:** v0.5.0 integrated normalized GP with fixed bulk nonlinearity `mu=1` while treating `xi` as an independent initial-profile width. That allows an initially narrow core to expand toward the intrinsic bulk healing scale. v0.6.2 instead evolves `i Psi_T = -0.5 Laplacian(Psi) + mu (|Psi|^2-1) Psi` with `mu=1/(2 xi^2)` by default, matching the `tanh(d/(sqrt(2)*xi))` initial profile to the **exact planar black-soliton width convention**. This does *not* ensure the knotted 3D vortex is stationary. `--legacy-normalized-gp` restores the historical `mu=1` equation explicitly for regression only.
- Changing `xi` in v0.6.2 changes `mu`, and thus the physical GP model and its bulk Bogoliubov dispersion. **The xi=0.24 cases are model/core sensitivity tests, not grid-only convergence at fixed dynamics.** The B160/B192/B256 xi=0.28 ladder holds `mu` fixed, as required for the grid comparison. Compare frequencies only in an explicitly fixed unit convention.

## Preflight matrix

| Case | xi | Cells / xi | xi*kappa_max | xi / screened gap | Geom. G32 | Role |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| A160 | 0.08 | 1.28 | 0.134 | 0.282 | **FAIL** | 160^3 diagnostic |
| B160 | 0.28 | 4.48 | 0.286 | 0.246 | PASS_SCREEN_ONLY | primary preflight |
| B192 | 0.28 | 5.38 | 0.286 | 0.246 | PASS_SCREEN_ONLY | refinement |
| B256 | 0.28 | 7.17 | 0.286 | 0.246 | PASS_SCREEN_ONLY | high resolution |
| A320 | 0.08 | 2.56 | 0.134 | 0.282 | **FAIL** | diagnostic refinement |
| A512 | 0.08 | 4.10 | 0.134 | 0.282 | PASS_SCREEN_ONLY | VERY high memory |

G32 thresholds: `xi/dx>=4`, `xi*kappa_max<=0.30`, `xi/d_nonlocal<=0.30`. Values are from pinned **previous v0.6.1** user JSON results, and are **recomputed from the full centerline on each run**. Screening gap is *not a certified reach*, and thresholds are development choices.

At N=160, the required resolution entails xi>=0.25, whereas A requires xi<=0.08524 from its screened nonlocal gap. Therefore **no xi passes A160 G32**: choosing a numerically convenient value would conceal a failed precondition.

## Run (Windows, recommended order)

1. Unzip into a new `A069-v0.6.2_DEVELOPMENT` folder. Do not overlay v0.5.0.
2. Install the dependencies:

```bat
py -m pip install -r requirements.txt
py bootstrap_upstream.py
py -m pytest -q tests
py plan_v062.py
```

3. The initial 160^3 runs, **B then A**, with separate run IDs and 8-step GP snapshots (the A run has a mandatory explicit diagnostic override):

```bat
run_preflight_160.cmd
```

Equivalent manual commands:

```bat
py run_v062.py --case B160 --steps 16 --save-checkpoints
py run_v062.py --case A160 --steps 16 --allow-unqualified-geometry --save-checkpoints
```

4. Optionally run B192 and B256 grid-only refinement sequentially, after reviewing RAM with `py plan_v062.py`:

```bat
run_optional_high_res.cmd
```

5. Optional separate temporal and core-scale variation campaigns (new run IDs, not merged with grid-only comparison):

```bat
run_time_refinement.cmd
run_optional_core_refinement.cmd
```

6. If your computer has sufficient RAM (forecast > 82 GiB) and storage for the **A512** *diagnostic* research route, run it **manually**:

```bat
py run_v062.py --case A512 --steps 16 --save-checkpoints
```

**Do not disable RAM safeguards merely because the PC has many CPU threads.** A512 may need 96–128 GiB available RAM, hours of compute, and substantial disk. A320 has fewer requirements but still fails the geometry-screening resolution criterion. If A512 is impractical, the next engineering improvement should be a localized/adaptive-grid GP implementation, not a pretend 160^3 qualification.

## Runtime behavior

- SHA-256 checks the pinned v0.5.0 PUBLIC source archive (`bb8e1d392e3e72c0c2caee22df406469f9f3de5504296da45cedc6fda8d04b6e`). The raw full A/B centerline is generated by the unchanged v0.5.0 solver; KnotPlot-relaxed exports are not admitted as physical evidence.
- Performs actual **3D GP split-step evolution**, mass and Hamiltonian audit, oriented face winding, bilinear subgrid face zeros, dual graph cycles, two spectral subcell-offset checks, and multi-projection Fox determinant diagnostics for unambiguous closed reconstructed filaments.
- The projection determinant of one reconstructed snapshot is **not** a proof of ambient isotopy during continuous evolution. Cross-grid pointwise convergence and independently established topological transport remain open.
- Stores run-unique JSON records and optional run-specific `.npz` checkpoints, including source-hash and settings. Resume uses `--resume-from <checkpoint.npz> --steps <larger_total_step_count>` and reports a **partial continuation**, never a new independent scientific observation. Do not overwrite a historical result.
- Memory guard estimates ~4 GiB at 160^3, ~5.8 GiB at 192^3, ~11.7 GiB at 256^3, and ~82.8 GiB at 512^3, **plus conservative available-RAM reserve**. Actual peaks depend on FFT, SciPy, Numba, OS and memory fragmentation. `--allow-memory-overcommit` is a hazardous override.
- The default 16-step run (`dt=.003`, `T=.048`) is a **short preflight**, not a long-duration stability study and certainly not four internal oscillation cycles.

## Independent blind gate map

- **G32**: core-size/curvature/nonlocal separation/mesh readiness: fail closed if violated. `PASS_GEOMETRY_SCREEN_ONLY` is not a framework scientific PASS.
- **G33**: face-zero/dual graph checks, subcell shifts and numerical projection consistency: diagnostic only.
- **G34**: cross-grid/time/core/domain convergence, continuous isotopy, reconnection tracking: `UNRESOLVED` for all current campaigns.
- **G35**: stationary/RPO base, physical Floquet/BdG eigenmode, >=4 cycles in independent holdout: `UNRESOLVED`.

## Evidence and versioning

- `provenance/` includes two original v0.6.1 user diagnostic JSON records as separate read-only baselines (not independent physical providers).
- `upstream/` contains the original public v0.5.0 source ZIP. `a069_v061` and older tests are inherited unchanged, with new `campaign_v062.py` and `projection_topology_v062.py`.
- The v0.6.1 and v0.5.0 official outputs are **not changed or relabeled**.
- This development package is **not a BLIND framework run**. Scientific preregistration, complete convergence and a truly independent holdout are required before any qualification or reveal.
