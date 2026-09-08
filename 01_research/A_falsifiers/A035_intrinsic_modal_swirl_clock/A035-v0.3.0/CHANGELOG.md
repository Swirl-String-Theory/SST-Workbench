# v0.2.2.8

- Replaced Windows batch parsing in `run_focus_topology.cmd` with a Python-owned `focus_runner`.
- The `.cmd` now forwards `%*` verbatim; argparse handles `--libraries=Gilbert,Katlas`, `--min-carriers`, `--kind`, and topology selection.
- Adds regression tests for the exact user command line and the spaced option form.
- No physics/kernel/gate changes.

# v0.2.2.7

- Fix Windows `run_focus_topology.cmd` argument forwarding: comma-separated `--libraries=Gilbert,Katlas` is now parsed and re-quoted instead of reconstructed as an unsafe free-form `%EXTRA%` string.
- Focus script now creates `outputs\` before shell redirection.
- Correct package metadata version in `pyproject.toml` to 0.2.2.7.
- No physics, numerical gate, parser, translator, or native-kernel changes.

# Changelog

## v0.2.2.6 — Long-run progress / ETA observability

- No physics, recurrence-gate, source-selection, blinding, mesh-controller, core-law, or integrator changes.
- Per-candidate `START`, `RUN`, `DONE`, `SKIP`, and `ERROR` console progress.
- Default 15-second heartbeat while a single trajectory is still running (`progress_heartbeat_seconds`).
- Reports anonymous candidate/carrier ID, probe arm, component count, output `.npz`, RK4 step progress, simulated time, candidate elapsed time, branch elapsed time, and approximate candidate/branch ETA.
- Appends the same progress to `outputs/<run>/progress.log`, including timestamped branch BEGIN/END records.
- Blindness is preserved: source-library identity, topology identity, and private source path/file are never printed before reveal.
- ETAs are deliberately marked `~` because cost varies strongly with geometry and planned RK4 step count.

## v0.2.2.4 — Katlas PD-link translator + source-family carrier threshold

- Add `SST-KATLAS-PD-3D-1.0` for Katlas links. The exact KnotTheory PD rotation system is embedded planarly; `(i,k)` is lower and `(j,l)` upper for `X[i,j,k,l]`; only intended crossings receive a z lift.
- Require the generated multi-component count to match Katlas' independent Gauss-code component count.
- Katlas root is now `..\..\Katlas_Sources_v0.2.2_Outputs`, so both `knots` and `links` are discovered.
- Add `--min-carriers=N` to `scan-provenance` and `prepare-provenance`. A carrier means a distinct source family for a topology; multiple Fremlin variants remain separate shape seeds but one carrier.
- Add `--kind=all|knots|links`.
- Add `run_links.cmd`, defaulting to `Gilbert,Katlas --min-carriers=2 --kind=links`.
- Keep the C++ Biot-Savart/stretch physics unchanged.
- Add NetworkX as a source-preparation dependency for exact planar-embedding of PD rotation systems.

## v0.2.2.3 — Library selector + Katlas canonical-braid translator

- Add `run_all.cmd --libraries=Fremlin,Gilbert,Katlas` and selector support in `scan-provenance` / `prepare-provenance`.
- Explicit selection reads only the named libraries; KnotPlot is fully skipped unless `KnotPlot` is selected.
- Update official Fremlin root to `..\..\Ideal_Fremlin_Fseries\fremlin`.
- Add Katlas root `..\..\Katlas_Sources_v0.2.2_Outputs\knots`.
- Add `SST-KATLAS-BRAID-1.0`: parse Katlas `BR(n,{...})`, construct a smooth closed-braid 3-D seed, preserve exact braid word and compact PD/Gauss/DT/invariant audit metadata.
- Katlas geometries are explicitly marked `generated_from_katlas_braid`, `source_coordinates=false`; no claim that Katlas supplied metric coordinates.
- Translation is deliberately limited to explicit braid records. In the supplied Katlas library this gives 250 unique knots through 10 crossings; 11/12-crossing PD/Gauss/DT-only records remain metadata-only.
- Deduplicate duplicated Katlas crawler paths by `(kind, katlas_id)`.
- Explicit multi-library runs default to the intersection of selected libraries; `Fremlin,Gilbert,Katlas` yields 34 official matched knot topologies with the current archives.
- Fremlin variants remain separate shape seeds but one opaque source-family vote. Gilbert and Katlas each contribute one source-family vote.
- No Biot-Savart kernel, recurrence gate, mesh gate, core law, or Stage-B physics changed.


## v0.2.2.2 — Official-source + Fremlin-variant compatibility hotfix

- Correct the official Gilbert IdealLinks container tag to `<TL>`; retain tolerant `<HL>/<LINK>` support only for mirrors/conversions.
- Auto-discover the complete official Ideal source family when present: `Ideal.txt.gz`, `Ideal_11a.txt.gz`, `Ideal_11n.txt.gz`, `IdealLinks.txt.gz`, 10-crossing link catalogs, and split 11-crossing link catalogs.
- Fix canonical parsing of `K11a*` / `K11n*` record IDs.
- Preserve all official Fremlin shape variants within a topology (e.g. `3_1`, `3_1p`, `3_1u`; `6_3d`, `6_3z`) instead of truncating to one.
- Cross-provenance voting is now balanced by opaque source family: multiple Fremlin variants are tested independently but count as one provenance family against relaxed/Ideal.
- Add blind `provenance_group_id`; actual source-family identity remains hidden until reveal.
- Source scan now reports per-topology variant counts and all discovered official Ideal catalog files.
- No Biot--Savart physics, recurrence thresholds, mesh controller, core law, or Stage-B causal gates changed.

## v0.2.2.1 — superseded parser hotfix

- Superseded: v0.2.2.1 incorrectly described the upstream IdealLinks parent as `<HL>`; official upstream bytes use `<TL>`.
- Its multi-component `<STRING>` handling and verified link aliases remain valid and are retained.

## v0.2.2 — Seed-Provenance + Mesh-Certified Modal Clock

- `run_all.cmd` now performs matched relaxed/Fremlin/Gilbert provenance testing.
- Default source roots: `..\..\KnotPlot\knots\final`, `..\..\KnotPlot\Knots_FourierSeries`, `..\..\Ideal_Sources`.
- Direct `.gz` readers for `Ideal.txt.gz` and `IdealLinks.txt.gz`; no manual extraction required.
- Added Fremlin six-column `.fseries` reconstruction.
- Added Gilbert AB/HT Fourier reconstruction with omitted-zero coefficient support.
- Added true multi-component IdealLinks support: separate closed strings, indexed C++ self+mutual Biot-Savart, no concatenation bridge.
- Link mesh `ds_cv` is evaluated per component and max-reduced.
- Added anonymous `topology_group_id` and blind seed-provenance robustness analysis.
- Added `blind_provenance_results.csv`, `blind_provenance_summary.json`, and post-reveal `revealed_provenance_results.json`.
- Fixed v0.2.1 floating-point mesh-cap rejection (`1.5000000000000004 > 1.5`) with explicit numerical tolerance.
- Nominal mesh/physical RMS cap raised to 2.0; candidate-only low/high gauge replays vary both gain and cap (0.7x / 1.3x) before certification.
- Added `run_provenance_scan.cmd` and `run_focus_provenance_3p1.cmd`.
- Retains strict `ds_cv <= 0.20`; no post-hoc gate relaxation.
- Native C++ remains MSVC-safe (`py::ssize_t`; no unqualified `ssize_t`).

## v0.2.1 — Numerical-Certification / Parameterization-Invariance Hotfix

This release changes **numerical certification**, not SST physics.

The v0.2.0 BASIC campaign showed that a global `FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK` was too strong: only 3/49 carriers passed the strict long-horizon geometry gate, and all three predeclared high-information carriers failed to remain certifiable to `T=24`.

### Fixed: coverage-aware negative verdicts
- A global negative Stage-A verdict now requires:
  - at least 80% geometry-valid carriers in BASIC/EXTENDED;
  - at least 20 valid carriers;
  - **all predeclared priority carriers geometry-valid**.
- Otherwise the gate is:
  - `INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE`.
- Focus runs use 1/1 coverage; the resolution trio uses 3/3 coverage.

### Fixed: parameterization-invariant modal observable
Every Stage-A snapshot is analysis-only canonicalized by:
1. uniform closed-curve arclength resampling;
2. cyclic parameter-origin alignment;
3. rigid Kabsch alignment;
4. normal projection.

Thus POD no longer follows bead-index drift created by the tangential mesh gauge.

### Improved tangential redistribution
- Replaced the default target-point projection controller with direct segment-length feedback:
  `alpha[i+1]-alpha[i] = -k (ell[i]-mean(ell))`.
- Applies only `u_mesh = alpha t_hat`.
- Optional legacy `target_projection` method remains for audit.
- RMS mesh speed is capped relative to physical Biot-Savart RMS speed.
- Strict `ds_cv <= 0.20` certification gate is retained; it is **not relaxed**.

### New mesh-gauge certification
A provisional recurrent Stage-A mode is replayed only on that anonymous carrier with:
- lower redistribution gain (`0.6 x nominal`),
- higher redistribution gain (`1.4 x nominal`).

The frozen nominal mode must remain recurrent and its period, closure and amplitude must remain within predeclared spread gates. Only then is it promoted to `stage_a_candidates.json` and allowed into Stage B.

### High-information carrier coverage
The following source patterns are predeclared before blinding:
- `knot_6.3_final`,
- `link_4.2.1_final`,
- `link_9.2.20_final`.

The blind scorer sees only a `certification_priority` role flag, never the source identity.

### Progress logging
Long branches now emit anonymous per-candidate progress:
`[stage_a 017/147] ... t=... ds_cv=... stop=... mesh/phys=...`.

### Chain
BASIC is now 9 stages:
prepare -> nominal Stage A -> provisional analysis -> low/high mesh-gauge replays -> gauge certification -> material/fixed Stage B -> final analysis.

### Retained safeguards
- `T_A=24` BASIC, `T_A=36` EXTENDED.
- absolute `discovery_time=1.2`.
- RK4.
- hard `dt ~ ds^2` step-cap policy; no hidden timestep coarsening.
- `py::ssize_t` Windows/MSVC guard.

## v0.2.0 — Long-Horizon Mesh-Stabilized Recurrence Gate

Introduced Stage-A-first recurrence, `-/0/+` probe arms, natural + odd modal channels, tangential mesh stabilization, multi-return closure, fixed absolute discovery window, and candidate-only material/fixed Stage B.

## v0.2.2.6
- Added `--topology=` to provenance scan/prepare.
- Added `run_focus_topology.cmd`.
- Canonical CLI aliases include `3_1`, `K3.1`, `L2a1`, and `L2.2.1`.
- Fixed focus-script bootstrap.
- Physics/native kernel unchanged.
