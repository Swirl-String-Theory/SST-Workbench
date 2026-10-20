# A003 v0.3.0 — PKLSA Carrier Registration + Temporal Dynamics

**Development / numerical qualification only.** This release keeps the frozen A003 v0.1.2 atlas (manifest SHA256 `01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d`), the validated bounded G5 v0.2.8.1 baseline, and external `SST_Falsifier_Framework_v1.0.10` unchanged. Do not treat the E010 source-contract overlay as a committed canonical E010 release, or a regularized vortex-filament trajectory as an incompressible Euler solution.

## Native implementation — no parallel Biot–Savart kernel

- **G6P6** imports the actual `E010-v0.3.1/sst_pklsa` package (unique import namespace, version checked) and calls **`Workbench.open(root, contract=overlay).resolve_sources()`** with a run-local extension of the existing `source_contract_production_v2.json` (or v1 fallback). The A003 source path is canonical relative to the Workbench. Eight F3/F4 XYZ carriers across N=1200,2400,4800,9600 are assigned exact SHA256, source family, resolution, and **two correlated analytic independence groups**. A clean source contract overlay and carrier ledger are produced; **no E010 configs or canonical registry files are modified**. The E010 API currently inspected does not provide a persistent carrier write interface. G6P8 stays UNRESOLVED.
- **G6P7** imports `C005-v0.6.1/fermat_ext.core.backend_biot_savart()` and evaluates it at **each of the four stages of classical RK4** on the evolving polygon. The integration equation is

  `dX_i/dt = u_C005,epsilon(X(t))[X_i(t)]`.

  Time is **source-unit model time**, not SST absolute physical time. The C005 `beta0/2` coefficient and arbitrary `epsilon=0.05` remain **uncalibrated**. No distinct Biot–Savart kernel is implemented or embedded.
- Default bounded temporal ladder: F3/F4, N=150,300,600, all derived by deterministic decimation from verified **uniform_t N=1200** seeds; **same final time T=2**, RK4 time steps T/4,T/8,T/16 for 150/300 and a finest 16-step trajectory for 600. G5's N=1200/2400/4800/9600 four-resolution qualification is preserved separately. `--full` performs an extra N=1200/16-step diagnostic, not a complete high-resolution convergence study.
- All generated trajectories, checksums, independent source hashes, step counts, numerical spatial/temporal differences, framework ledger, and an automatic PDF are written into a unique immutable run folder.

## Windows Workbench layout

Install this ZIP as a sibling to A003-v0.1.2:

`C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\A003_Fourier_Knot_Import_Adapter_v0.3.0`

E010 is expected under

`01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.1`

C005 is expected under

`01_research\C_dynamics\C005_fermat_biot_savart\C005-v0.6.1`

Framework is expected under

`06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`.

From an activated compatible `.venv`:

```bat
run_all.cmd
run_all.cmd G6
run_all.cmd COMPLETE
run_all.cmd G6_FULL
```

- `run_all.cmd` is the original atlas audit/unittest command.
- `run_all.cmd G6` executes the E010/C005 temporal diagnostic using the latest verified earlier G5 receipt.
- **`run_all.cmd COMPLETE`** runs a fresh G5 four-resolution qualification, then G6, without suppressing scientific FAILs. A hard provenance/manifest failure stops the run.
- `run_all.cmd G6_FULL` additionally evolves N=1200 with 16 steps. This is intentionally expensive.
- `run_all.cmd FULL` retains the legacy audit + G5-only meaning.

For custom paths and numerical parameters:

```bat
run_g6_pklsa.cmd --g5-summary "C:\path\QUALIFICATION_SUMMARY.json" --final-time 2 --epsilon 0.05
```

Exit code `3` means **G6 unresolved**, despite numerically successful G6P6/P7. Exit `2` indicates a scientific gate FAIL; missing source/hash pin normally raises a fatal exception. Do not mistake code `3` for an infrastructure failure.

## Gate interpretation

| Gate | Meaning | Expected outcome with installed sources |
|---|---|---|
| G6P0 | v1.0.10 pinned `gates.py` and **local** canonical freeze metadata | PASS only if local RELEASE_INFO is CANONICAL_FROZEN |
| G6P1 | A003 frozen 384-XYZ source integrity and real G5 receipt | PASS if G5 qualified; FAIL if intact negative scientific receipt |
| G6P2 | E010 v0.3.1 source API loaded and overlay resolved | PASS / diagnostic |
| G6P3 | C005 v0.6.1 native source kernel called for the ODE RHS | PASS / diagnostic |
| G6P4–P5 | trajectory spatial convergence and positive sampled vertex separation | PASS / diagnostic, NOT full topological invariance |
| **G6P6** | E010 run-local **native** contract registration and eight immutable analytic carrier records | PASS if source checks succeed; **not canonical persistence** |
| **G6P7** | real RK4 evolution and halving/resolution comparison | PASS if numerical gates pass; **not Euler PDE** |
| G6P8 | canonical E010 registry commit | UNRESOLVED (never silently edits upstream) |
| G6P9 | Euler/pressure-Poisson/core calibration, full 3D topology/reconnection and time dynamics | UNRESOLVED |
| **G6** | physical PKLSA/Euler qualification | **UNRESOLVED** |

### Scientific limitations

An analytic generated F3/F4 seed is **not** independent experimental data, and the four resolutions are not four independent sources. Monitoring nonadjacent vertex distances cannot exclude all segment reconnections. No adaptive remeshing, energy/helicity closure, Euler pressure-Poisson constraints, physically established finite-core radius, physical time calibration, Kelvin/Floquet stability, or blind physical falsifier is supplied here. E010 resolution is native to the software package but its canonical upstream registry has not been modified.

The source identity of v1.0.10 is pinned by `FRAMEWORK_PIN.json`; the earlier Drive `RELEASE_INFO.json` reported `LOCAL_VALIDATED_CANDIDATE`, whereas the user's installed release reported `CANONICAL_FROZEN`. The runner uses the installed status and does **not** silently rewrite it.

### Files produced per G6 run

- `G6_TEMPORAL_SUMMARY.json`, `GATE_LEDGER.json` (Framework v1.0.10)
- `E010_A003_RUNTIME_SOURCE_CONTRACT.json`, `E010_A003_CARRIER_LEDGER.json`
- `G6_TEMPORAL_DIAGNOSTICS.json`, `G6_TEMPORAL_TRAJECTORIES.npz`
- `A003_v0.3.0_G6_TEMPORAL_REPORT.pdf`, `PDF_RENDER.json`
- Optional `G6_FULL_N1200_DIAGNOSTIC.json`

All files are written under sibling `A003_Fourier_Knot_Import_Adapter_v0.3.0-outputs/<run_id>/`, never over historical runs.

### Validation

Local development/fixture test: exact A003-v0.1.2 XYZ, measured previous v0.2.8.1 G5 receipt, the fetched E010 v0.3.1 resolver source, C005 v0.6.1 Python field kernel, and the real pinned Framework v1.0.10 `GateLedger` were exercised. G6P6/P7 passed locally; G6P0 did not because the local test fixture was deliberately labeled candidate. This is **not** a certification of the user's full native Windows source tree or physical Euler dynamics. Run `COMPLETE` locally and inspect `G6_TEMPORAL_SUMMARY.json` before promoting any claim.
