# E010 PKLSA v0.3.2 — DYNAMICS_READY extension (development)

This is **a versioned patch to the existing E010 `pklsa_builder`**, not another knot geometry library. Install it to a **new** sibling `E010-v0.3.2` directory using `install_into_e010_v032.py`. Unmodified E010 v0.3.1 and E011 v0.3.0 outputs remain read-only, with SHA-256 evidence.

The existing `pklsa_builder.gilbert`, `io_geometry`, and `geometry` modules load each source **natively**. E011's `STATIC_READY_PROVIDER_ANCHORS.jsonl` and unchanged `SEED_CONTRACT_SCHEMA.json` serve as the only admission source. No physical-dynamics capability is inferred from static eligibility. `gilbert_ab_record`, `xyz`, `vect`, `fseries` supported; closed single-component filaments only. Mirrors, generated controls, aliases, links and missing/mismatched source bytes fail closed.

**Numerical model:** free-space regularized midpoint Biot–Savart with Rosenhead kernel, RK4, independent spatial velocity refinement and three temporal trajectories (dt, dt/2, dt/4), regularized current-current energy diagnostic, approximate nonlocal clearance, core resolution. This is not the full 3-D Euler PDE, nor the A069 GP model. A `DYNAMICS_READY` result means **a verified short-horizon numerical readiness for this one specified finite-core filament model**, not stability of an SST particle, topology proof, equivalence to Euler, or an emergent internal clock.

A FULL run requires unmodified source sha, E011 admission, numeric thresholds, >=256-point fine grid, fixed core radius fraction 0.017 (when L=1), normalized Gamma=1, >=8 RK4 coarse steps and normalized T >=0.004. BASIC runs always return `DYNAMICS_NOT_READY` even when numerical checks pass. Any source conflict emits REJECTED and no scientific PASS. Pre-registered thresholds are in `pklsa_builder/dynamics_ready.py`.

## Install (Windows)

```
py install_into_e010_v032.py --e010-v031 "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.1" --target "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.2"
cd /d "C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.2"
run_all.cmd SELFTEST
run_all.cmd BASIC
run_all.cmd FULL
```

The raw BASIC qualifier returns scientific exit code **2** (`DYNAMICS_NOT_READY`), but the new `run_all.cmd BASIC` wrapper returns 0 after recording that expected diagnostic result. A technical execution failure returns code **3**. `run_all.cmd FULL` returns **0** only for `DYNAMICS_READY` and **2** for a numerically disqualified run. Outputs are uniquely named and create-only.

You can override original archive location using `PKLSA_E010_ZIP`, `PKLSA_E011_ZIP` and Python interpreter via `PKLSA_PYTHON`. If the source is installed at a different absolute path, use Python `--source-override` only when its raw SHA-256 equals the E011 locator hash. Original data are not modified.

## Framework v1.0.10 diagnostic export (optional)

Once a `*_RUN_RESULT.json` is generated, you can export the same eight registered DYN gates through the **real** v1.0.10 `GateLedger` (not a hand-coded fake ledger):

```
python emit_framework_v110_ledger.py --framework-root "C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10" --run-result "results\your_FULL_RUN_RESULT.json" --out "results\your_FULL_GATE_LEDGER_V110.json"
```

The emitter checks the framework's release version and module origin. This is **only a supplemental framework ledger**: the complete frozen v1.0.10 instance protocol, independent blind source freeze and certified PDF are not provided by this patch.

**Important:** only the NEW v0.3.2 copy receives a new `run_all.cmd` dispatcher. Its original v0.3.1 static entrypoint is preserved as `run_all_E010_v031.cmd` and available through `run_all.cmd STATIC`. E010-v0.3.1 is never modified. The dynamic entrypoint remains `run_dynamics_v032.cmd`. Framework v1.0.10 can consume the external result using `GateLedger` but this development patch is not an official frozen framework instance.

## Evidence boundaries

`G1/G2/G3` original E010 PASS are retained without restamping. Gilbert B1=FAIL is carried through as source diagnostic and **never silently promoted**. E011 static readiness remains unchanged and `dynamics_ready` remains false in its original `SEED_CONTRACT_SCHEMA.json`. Dynamic new output is separate `E010-PKLSA-DYNAMICS-READY-1` with observed test gates and fail-closed status.

The model assumes a prescribed circulation and a finite-core regularization; it does **not** derive those from SST. It makes no claims about 3-D Euler invariants, physical reconnection, Kelvin/Floquet modes, source independence beyond one original anchor, or Swirl Clock frequency.
