# Runbook — Workbench 1 / v0.2.0

## 1. Install

```cmd
run_00_install.cmd
```

The script prefers `C:\workspace\projects\SST-Workbench\.venv`. Edit `config\paths.cmd` only if the workspace moves.

## 2. Confirm C++

```cmd
run_01_check_backend.cmd
```

Desired result:

```json
{"backend":"cpp","native":true}
```

If it reports `python`, the basic workflow is still valid as a geometry/proxy audit. For extended runs, install Visual Studio C++ Build Tools and rerun `run_00_install.cmd`.

## 3. Basic run

```cmd
run_10_basic.cmd
```

This is the first run to inspect. In particular check:

1. `discovered_files.csv` — were all intended `.vect` files parsed?
2. `geometry_metrics.csv` — are `segment_cv`, `length_units`, curvature and writhe stable/plausible?
3. `mode_candidates.csv` — candidates should be tagged `GEOMETRY_CANDIDATE_NOT_EIGENMODE`.
4. `interaction_coupling_proxy.csv` — inspect translation/rotation/shape fractions and dominant Kelvin candidate.

A positive coupling proxy is **not yet a thermodynamic mode**.

## 4. Extended run

```cmd
run_20_extended.cmd
```

Preset:

- resample `N=1200`;
- Fourier deformation index `m=1..16`;
- source orientations `0,45,90,135 deg`;
- impact parameters `0,0.35 R_rms`;
- separations `3,4 R_rms`;
- regularization radius `0.05 R_rms`;
- self-pairing by default.

This yields 16 encounter probes per parsed curve.

## 5. Cross-knot campaign

Only after the self-pair run is sane:

```cmd
run_21_extended_unique_pairs.cmd
```

This scales approximately with the number of unique knot pairs and is intentionally separated from the normal extended run.

## 6. Strict physical falsifier

v0.2 writes:

```text
outputs\extended\v01_physical_campaign_skeleton\
```

The following remain blank until a physical solver provides them:

- mode `omega_rad_s`;
- `gap_eV` and its physical status;
- `tau_s`;
- encounter `delta_energy_eV`;
- amplitude-energy scans;
- energy ledger;
- spectroscopic couplings/limits.

After those are populated and preregistered:

```cmd
run_30_physical_falsifier.cmd <config.json> <outdir>
```

The strict three-gate logic remains:

```text
coupled AND drive_energy >= gap AND tau <= observation_time
```

with the independent amplitude-scan guard against claiming a positive gap on a branch whose excitation energy tends continuously to zero.
