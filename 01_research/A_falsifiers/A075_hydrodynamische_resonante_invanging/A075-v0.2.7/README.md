# A075-v0.2.7 — Gate, Source & Boundary Qualification (Framework v1.1.0)

**DEVELOPMENT_ONLY / PHYSICAL_ANSWER_UNRESOLVED.** New gate/source/boundary qualification version based on A075-v0.2.6 (whose physics originates from v0.2.4). The true v1.1.0 `sst_falsifier` runtime and `instance_template/native/cpp/sycl_worker.cpp` have been copied from the user-connected canonical v1.1.0 Google Drive source into `_sst_runtime/`, with a byte-exact `RUNTIME_SNAPSHOT_MANIFEST.json`. The instance bootstrap refuses silent global-framework fallbacks.

## Unchanged physical methodology

The fully three-dimensional incompressible periodic Fourier-Galerkin Euler solver, adaptive RK4, donor/control paired energy ledger, 0_1 and analytic 3_1, strict original-source gating for 5_2 and 6_1, native C++ hybrid, Intel XPU Euler implementation, and opt-in periodic-domain-size tests are retained from v0.2.4. **Periodic boundaries remain the default; free-space is NOT implemented.** No scientific gate is promoted based on the migration.

## Framework v1.1.0 mandatory 2-of-3 execution contract

`experiment/backend_matrix.py` runs the *actual source/no-source Euler time evolution* on each available backend using the same 0_1 initial field, grid, physical final time and numerical controls. The backend matrix records `python`, `pybind11` (compiled C++ nonlinear kernel), and `torch_xpu` (actual Arc device). It saves source/build/evidence SHA-256 and a shared input hash. v1.1.0 validates these and **requires at least two real scientific backends**; probes never qualify. GPU FP32 and CPP hybrid evidence are numerical diagnostics, not independent continuum or physical proof. No CPU fallback substitutes an unavailable GPU.

## Windows quick start

Extract to `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\` as **new** `A075-v0.2.7`. In the previously validated `.venv-a075-xpu` Python environment:

```bat
cd C:\workspace\projects\SST-Workbench
.venv-a075-xpu\Scripts\activate.bat
cd 01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.7
python -m pip install -r requirements.txt
python -m pytest -q tests
python tools\check_sources.py
python tools\preflight_contract.py
python tools\build_native.py
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd GPU_PROBE
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --grid-up 112 --threads 12 --allow-expensive
```

`BACKEND_PREFLIGHT` triggers hardware/native compilation probes, not full physics. The subsequent `BASIC` runs the canonical v1.1.0 science adapter with the mandatory three-backend attempts; framework return code 3 means fewer than two valid scientific executions and is NOT a physics finding. Heavy runs need explicit budgets and original XYZ files for extended knot cases. `run_all.cmd BASIC --plan` shows the cost without running. `run_all.cmd FULL --plan` likewise.

Optional periodic box sensitivity **without changing the main method**:

```bat
run_all.cmd BASIC --domain-study --domains 10:80,15:120,20:160 --knots 0_1 --threads 12 --allow-expensive --plan
```

`--domain-study-only` is a separate explicit diagnostic through `run_all.cmd BASIC --domain-study-only`; it saves outside canonical BLIND output and cannot satisfy the v1.1.0 two-backend execution contract. Source folder and `preregistration/FROZEN_PROTOCOL.json` must remain separate for every version.

## Outputs and interpretation

Canonical output `A075_Hydrodynamische_Resonante_Invanging_v0.2.7-outputs/` contains `AUTO_BACKEND_MATRIX.json`, `backend_science/{py,cpp,gpu}.json`, diagnostic energy matrices, `GATE_LEDGER.json`, manifests and a framework PDF report where the installed renderer permits it. Stable archives use `A075_Hydrodynamische_Resonante_Invanging_v0.2.7-outputs__<run-id>_BLIND.zip` and corresponding SHA-256 manifests; private reveal stays separate. No long-time capture, free-space convergence, independently validated clock cycles or core-stability claims are made here.

## Live heartbeat (v0.2.7)
Zie `HEARTBEAT_GUIDE_NL.md`. `run_all.cmd STATUS` toont een JSON-momentopname; `--heartbeat-seconds 10` stuurt de niet-wetenschappelijke console-interval.

## v0.2.7 qualification additions

G1 resolves all three registered files from the actual Workbench root and compares expected byte-hashes. G5/G6 run small genuine operator-level C++ and Intel-XPU parity tests, separate from the required full source/control 2-of-3 backend matrix; G7 remains UNRESOLVED without independently checked original knot topology. G10 is an opt-in periodic-box sensitivity diagnostic; it cannot certify nonperiodic boundaries, post-exit retention or physical convergence. See `INSTALL_AND_GATES_v0.2.7_NL.md`.
