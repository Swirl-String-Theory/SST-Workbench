# SST Falsifier Framework v1.1.0 — Self-contained 2-of-3 Runtime

**Release status: DEVELOPMENT / target-machine certification pending**. Source lineage: complete manifest-verified v1.0.10 Canonical, historical v1.0.7 Canonical references, selective v1.0.11 automatic probes. No direct mutations of predecessor versions or existing frozen falsifiers.

Each new generated falsifier embeds `_sst_runtime/` with exact source-file SHA-256 hashes. No installed framework is required at run time. The local, fail-closed bootstrap verifies the runtime inventory and rejects corrupted or missing local sources. No global/Workbench fallback.

## Mandatory multi-backend execution contract

At least **two distinct scientific implementations** must actually execute among Python/NumPy FP64 (`py`), C++17/pybind11 (`cpp`), and GPU via Intel Arc XPU (`gpu`, default) or NVIDIA CUDA (`gpu`, explicit opt-in). Intel and CUDA are one GPU category. The three device probes themselves never count. Missing kernels, invalid hashes, changed input hashes, inconsistent physical final time, or a claimed CUDA computation on Intel (or vice versa) are NOT accepted. A 1-of-3 run publishes diagnostics but returns exit status **3**. Parity diagnostics are not evidence of Euler equilibrium, topological persistence, convergence or physical confirmation.

## Pipeline

`BACKEND_PREFLIGHT` / `ATLAS_VERIFY` -> `FREEZE` -> `BASIC` -> `FULL` -> `CERTIFY` -> optional policy-gated `REVEAL`. Each run has immutable ID, archived previous output, science/ledger/evidence manifests, detailed LaTeX PDF where available, ReportLab diagnostic PDF fallback, separate blind/revealed ZIPs with SHA-256. The template requires full scientific report text and methods before FREEZE; a sparse science stub cannot be certified.

## Geometry integration

Pinned read-only bridge `PKLSA_Universal_Atlas_Adapter_v0.1.0` -> `E010-v0.4.0`, located via `SST_WORKBENCH_ROOT`/`E010_ATLAS`. Never duplicate or rewrite the atlas. The adapter enforces raw SHA-256 and float64 geometry provenance and blocks research-only records until explicitly admitted. `ATLAS_VERIFY` uses existing adapter code and exact E010 pin; it does not create dynamics evidence. See `docs/INSTALL_WINDOWS_NL.md`.

## Create a new standalone instance

```bat
python tools\new_falsifier.py A080 ring_control C:\path\A080-v0.1.0 --profile gpu --version v0.1.0
cd /d C:\path\A080-v0.1.0
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd ATLAS_VERIFY
```

Complete the scientific protocol, reference bibliography, source contract, gate evaluators, and `experiment/backend_matrix.py` before FREEZE. A runnable **synthetic regularized Biot-Savart example** is at `examples/backend_matrix_biot_savart_control.py`; it is a numerical backend demonstration, NOT an SST physics falsifier. No automatic transfer of this synthetic example into new research falsifiers.

## Verification before Windows production admission

Run `python -m pytest -q tests`, instantiate an example with the generator, verify tamper rejection of `_sst_runtime`, perform 2-of-3 real Python/C++ and Python/Intel runs on the Windows Arc A770 system, separately test CUDA on the GTX 1060 if compatible, and visually inspect the PDFs. Record new target-machine hashes in an external certification artifact; do not relabel this release as canonical without those checks.
