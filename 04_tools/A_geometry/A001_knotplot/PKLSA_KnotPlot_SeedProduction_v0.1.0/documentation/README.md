# PKLSA KnotPlot Static Seed Production v0.1.0

**Result:** runnable local analytical geometry build; 16 dimensionless closed single-component trefoil embeddings, four families (A, mirror(A), B, mirror(B)) at N=128/256/512/1024. A build does NOT run KnotPlot, nor certify any Euler or finite-core dynamics. Build checked with numpy and Python's unittest. KnotPlot imported-file readback is explicitly outstanding.

## Intended Workbench placement

Source scripts: `04_tools/A_geometry/A001_knotplot/PKLSA_KnotPlot_SeedProduction_v0.1.0/`

Do not alter frozen `01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1`. Instead stage the `manifest.csv` and `RELEASE_CANDIDATE.json` as new *candidate* geometries for a future separately versioned E010 import. Each candidate receives source formula, parent seed, mirror lineage, provider group, N, SHA256, and qualification status; generated mirrors/resolutions do not increment independent provider counts. No synthetic fallback for PKLSA physical claims.

## Models

- A, notebook 2015 p.32: `(cos(t)+1.5cos(2t), sin(t)-1.5sin(2t), 0.35sin(3t))`
- B, notebook 2015 p.66: `((2+cos(3t))cos(2t), (2+cos(3t))sin(2t), sin(3t))`
- For each, exact mirror under `(x,y,z)->(x,y,-z)` and **same parameters** for downstream paired comparisons.
- Integration interval `[0,2pi)` once, no duplicate final bead.

Analytical length reference: `L_A≈19.976521977`, `L_B≈31.898600620`. Crossing height separation for A is `7 sqrt(2)/27≈0.366647960615`, not `7 sqrt(2)/54`. Signed xy writhe (fixed oriented over/under convention) +3 for A, -3 for B and sign flip for exact mirrors; a tiny fixed proper projection rotation is used for numerical tests to avoid crossings landing on a vertex. The projection test is a **regression for these known parametrizations**, not a universal knot invariant/isotopy certificate.

## Local build (Windows / PowerShell)

Requires Python 3.10+ and NumPy: `py -m pip install numpy`.

```
py -m unittest discover -s tests -v
py src/seedproduction.py --out production_out
```

`generate_static.cmd` does both. It fails rather than overwriting an existing nonempty output directory. A pre-generated sample resides in `example_release/`.

## Files

- `geometry/*.txt`: 17-digit ASCII XYZ, a single *closed* component with no repeated endpoint.
- `geometry/*.kpt`: `KnotPlot 1.0`/`LOCD` big-endian double-precision binary file with component and closure flag. This writer is checked by an independent byte-for-byte roundtrip decoder, **not yet** by the user's actual KnotPlot executable.
- `kpc_diagnostic/*.kpc`: read-only `reset all`, `load`, `information`, `length`, `parameters`, `coords` and ASCII save scripts. These have no `go` and do not change default slider settings.
- `manifest.csv`: source identity, SHA256, geometry metrics, QA, physical status.
- `RELEASE_CANDIDATE.json`: explicitly not a production-certified release.

To run one KnotPlot diagnostic locally, start KnotPlot at `production_out` as working folder, then enter `read kpc_diagnostic/notebook2015_A_base_N0256.kpc`. Alternatively use `-stdin` and `-nographics` if supported by your installation. Confirm in KnotPlot that `load` of `.kpt` and of roundtripped ASCII files gives precisely the same coordinates, component count and handedness; inspect `parameters` and the log. `checkpoints/` has been created by the generator.

**Do not assume that a successful Python LOCD roundtrip proves KnotPlot accepts LOCD.** The actual installed build must be checked (the official KnotPlot file format documents LOCD, but reader support varies with build).

## KnotPlot relaxation lane — calibrated, NOT AUTO-RUN

`src/make_knotplot_campaign.py` emits two independent kinds of scripts after you supply a *real* local `configs/runtime_calibration.json` with KnotPlot version, machine, measured `close`, measured `max_dr` and SHA-256 of the runtime parameter dump. It refuses `max_dr>=close`, but this necessary inequality is not a collision-safety proof.

1. `__01_PREP_AND_ONE_STEP.kpc`: load source, preserve reset-default sliders, `collision fast`, `fitto mindist 1.05*close`, save the prepared static seed **once** and take `go 1` as a separate safety diagnostic. The `fitto mindist` subcommand is included because it is known from local A058-v0.2.10, but must be verified for your exact executable. Do not conflate this rescaling with arclength resampling.
2. `__02_512_2048_DIAGNOSTIC_ONLY.kpc`: generated only with an explicit `--emit-production` flag. Reloads the **same prepared** seed and records 32, 128, 512, 2048 matched cumulative iteration states. Do not run until the prep has passed source integrity, non-collision and roundtrip checks in your local executable. All files stay `DIAGNOSTIC_ONLY`. No 8192/32768 stage is supplied until convergence criteria and additional resolution/holdout replicates have been fixed.

Generate calibration scripts (sample command, not executable until calibrated):

```
py src/make_knotplot_campaign.py production_out --runtime configs/runtime_calibration.json
```

For finite-budget scripts, separately invoke with `--emit-production` only **after** prep and go-1 verification. This does **not** assert a passed safety check; human review is mandatory. We do not reuse A058's chosen slider response values as optimal settings or change its frozen science contract.

## Historical latest KnotPlot exports

Keep archives **read only**, e.g. `03_data/A_knots/04_knotplot/final/` or local `KnotPlot/knots/final/`. Do not replace them. For a quarantine audit:

```
py src/audit_legacy.py "C:\workspace\projects\SST-Workbench\03_data\A_knots\04_knotplot\final" --csv legacy_quarantine_inventory.csv
```

The parser uses blank lines as component boundaries, calculates component lengths independently (not the anomalous KnotPlot `data /l` output), checks edge CV, SHA256 and byte duplicates. All old relaxed exports stay historical controls; their link component counts/topologies still require independent topology and isotopy gates.

Some Drive examples inspected in planning: `knot_3.1_final.txt` 300 points; `link_6.3.2_final.txt` 322/292/285 points; `link_6.3.3_final.txt` 323/280/296 points; `torus_3.3_final.txt` 300/300/300 points. These are *examples*, not a complete Workbench census, and are not bundled as user-controlled source files here.

## Gates for eventual qualified E010->PKLSA handoff

| Gate | Requirement | Current state |
|---|---|---|
| S0 | Original source records, frozen formulas, SHA256 and provider lineage | PASS generated source; archive originals require full byte verification |
| S1 | Closed, finite 3D components with stable edges | PASS 16 analytic generated samples |
| S2 | Chiral mirror parity and 3-crossing projection regression | PASS 16 analytic generated samples |
| S3 | Resolution ladder N=128/256/512/1024 and numerical consistency | AVAILABLE, not a solver-convergence gate |
| S4 | Installed KnotPlot binary load/roundtrip, no silent topology changes | NOT_RUN |
| S5 | Runtime A058-style calibration, matching params/steps, safety, independent seeds | NOT_RUN |
| S6 | Independent trefoil and link isotopy certificate (e.g., Alexander and exact linking) | NOT_RUN |
| S7 | Finite-core tube embedding and nonlocal clearance / reach / core-to-mesh gates | NOT_RUN |
| S8 | Euler/pressure-Poisson time/space/core/backend converged dynamics and phase | NOT_RUN |

Geometry status is not ropelength-optimality, stability, self-confinement, swirl-clock certification, fermionic pressure, or gravity.

## References (LaTeX-ready)

```
\bibitem{SchareinKnotPlot} R. G. Scharein, ``KnotPlot Manual,'' Hypnagogic Software, online manual, https://knotplot.com/manual/KnotPlotManual.html.
\bibitem{CantarellaRidgeRunner} J. Cantarella et al., ``Ridgerunner: a knot-tightening program,'' software documentation, 2022, https://github.com/designbynumbers/ridgerunner.
\bibitem{Saffman1992} P. G. Saffman, \textit{Vortex Dynamics}, Cambridge University Press, 1992, https://doi.org/10.1017/CBO9780511624063.
```

### Actual KnotPlot import/readback test

After KnotPlot executes one `kpc_diagnostic` file, verify the exported `coords` against the immutable source:

```
py src/check_knotplot_roundtrip.py production_out/geometry/notebook2015_A_base_N0256.txt production_out/checkpoints/notebook2015_A_base_N0256_roundtrip.txt
```

This requires identical component/bead counts and pointwise coordinate agreement; it does not silently optimize rotation or scale. Record the KnotPlot executable SHA-256 independently in the runtime provenance. A full original-source scan must similarly use raw file byte hashes, not only text-fetched content.
