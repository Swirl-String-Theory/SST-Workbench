# A069 v0.3.0 — 3D Swirl Clock Emergence

**Status:** Development / analytic and STATIC_READY metadata controls only. **Not physical clock certification.**

**Framework:** SST Falsifier Framework **v1.0.9** exclusively (generated instance pin).

## What changed
- Preserves and reruns inherited D1 affine 3D Euler and D2A smooth columnar controls with immutable v0.1.0 source SHA.
- **D2H:** new exact Hill 3D translating Euler vortex (interior/exterior, pressure, curl, circulation, U=Gamma/(5a)).
- **D2N:** new numerical dimensionless GP/NLS radial m=1 vortex with independent residual and gauge check. Straight vortex, not knotted, not clock.
- **D2R:** NLS ring *thin-core* E/P/U relation alpha=1.615 and proposed golden phi branch; no fat-core extrapolation.
- **D3 STATIC:** real E011-v0.3.0 atlas ZIP byte-hash pinned, selector filters historical KnotPlot, limits physical provider count.

The actual atlas contains a Gilbert ideal and a KnotPlot-relaxed provider for trefoil. Because the old relaxed data is inadmissible as physics evidence, only the Gilbert source can be eligible as upstream static geometry; the two-source physical replication gate is still closed. The E011 archive has carrier locators/hashes, not full dynamic trajectories or validated original-source sample bytes.

## Local commands

```bat
python -m pip install numpy scipy pytest
python -m pytest -q -o addopts="" tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd REPORT_ONLY
run_pklsa.cmd --topology 3_1
run_pklsa.cmd --topology 7_1 --historical-diagnostic
run_pklsa.cmd --atlas "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E011_sklsa_selected_knot_link_seed_atlas\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip" --topology 5_1
```

The ZIP is included under `sources/` for reproducible offline STATIC diagnostics, but no 3D PKLSA dynamic dataset is bundled. `run_pklsa.cmd` is an optional **read-only audit tool** and does not mutate a frozen BASIC run ledger. To include any new source or physical claim in an official experiment, create a new version and FREEZE a new science contract before seeing target results.

## Scientific statuses

- G0-G3,G12-G18: analytic/reference/static-manifest controls, `PASS` only if executed.
- G4-G7: disabled by minimal profile (NOT_APPLICABLE); untested physics cannot be promoted.
- G8-G11,G19: UNRESOLVED.
- E011 `STATIC_READY` != DYNAMICS_READY; Hill sphere is 3D but is not a knot and does not yield an atomic eigenclock.
- Gross-Pitaevskii is not automatically the canonical incompressible Euler SST medium; physical equivalence needs its own tests.

## Falsifier outputs

BASIC creates a separately hashed science evidence manifest and final output manifest plus a non-overwriting BLIND archive. Official reveal remains closed. `REPORT_ONLY` publishes a new PDF sidecar without modifying science evidence.