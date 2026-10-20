# A069 v0.2.0 — 3D Swirl Clock Emergence (PROVISIONAL CATALOG)

Research status: **ANALYTIC-CONTROL QUALIFIED; PHYSICAL SST CLOCK UNRESOLVED**.
Framework: **SST Falsifier Framework v1.0.9** (`CANONICAL_FROZEN` source, Windows Arc A770 backend qualification pending). Generated with the exact v1.0.9 `tools/new_falsifier.py` and a fail-closed relative locator; the runtime itself is **not bundled**.

## What is genuinely new

- Re-import and SHA-256 verify original D1-v0.1.0 result (hash `29ba1012aa3c20a3d94cf0e9898578aa0385d8f0c0986d490426035c0952f0dc`). Regenerate D1 independently, never count copied data as a new measurement.
- Execute exact steady **columnar** Euler D2A positive control: $u_\theta=Cr\exp[-(r/a)^2]$; vorticity, pressure gradient, finite kinetic energy *per axial length*, independent material tracer phase via two integrators, refinement and rotating-frame reconstruction. This remains **2D embedded in 3D**, NOT a dynamically qualified 3D knotted vortex.
- Separate gate evidence classes: D1 `analytic_control`, D2A `analytic_control`, experimental PKLSA clock `UNRESOLVED`.
- Preserve old KnotPlot visual relaxations and VortexLab proxy runs only as historical context, with no physical-admission route.

## Workbench placement

`SST-Workbench/01_research/A_falsifiers/A069_3D_SwirlClock_Emergence/A069-v0.2.0/`

Canonical runtime directory at `SST-Workbench/06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.9/`.

## Windows commands

```bat
run_all.cmd SELFTEST
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd REPORT_ONLY
run_all.cmd REVEAL_IF_ALLOWED
```

For full optional source/dynamic campaigns, a **new minor/patch release** must be created and frozen with the real E010/E011 PKLSA full 3D Euler sources. This v0.2.0 package intentionally contains no PKLSA time trajectories and cannot physically certify `G4..G11`. `BASIC` is an analytic control run only, not a physics test.

The directory `sources/A069_v0.1.0/` carries the exact parent D1 data. Its provenance is synthetic analytic-control, not independent scientific replication.

## Release/epistemic limitations

A v1.0.9 patch doesn't retroactively certify a v1.0.7-era scientific result. The official runtime freeze produces nonced source commitments, run-specific immutable science-evidence manifests and distinct BLIND PDF/ZIP outputs. If v1.0.9 is unavailable, STOP rather than falling back to v1.0.7. Its Windows native backends require `run_all.cmd ALL` in the separate framework folder.

A069 remains a provisional catalog ID until `catalog_index.json` and `family_hierarchy.json` are audited locally.
