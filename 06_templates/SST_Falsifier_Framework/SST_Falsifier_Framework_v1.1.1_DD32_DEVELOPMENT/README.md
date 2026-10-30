# SST Falsifier Framework v1.1.1 — DD32 DEVELOPMENT

**Status: DEVELOPMENT_NOT_HARDWARE_QUALIFIED.** This is a new source branch based on immutable v1.1.0 RC2 Canonical, not a replacement. See `docs/DD32_DEFAULT_WINDOWS_NL.md` for real Intel Arc and NVIDIA Pascal hardware tests. New instance GPU precision defaults to DD32 (FP32x2); native GPU execution is fail-closed. The long-standing v1.1.0 documentation continues below as parent-release context.

---

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

## A999 E010 release-candidate validation (v1.1.0 RC1)

`tools/prepare_a999_e010.py` creates a standalone, filled numerical integration
control from a single integrity-verified E010 v0.4.0 consumer export. `G10`
requires the Python reference and at least one genuinely executed C++/GPU
scientific implementation, **plus** preregistered numerical parity; a 2-of-3
execution count by itself is insufficient to certify this control.

`tools/verify_a999_release.py` checks the real `FULL` run, gate qualifications,
strict LaTeX PDF, immutable manifests, and blind ZIP sidecar. Exact Windows
commands are in `docs/INSTALL_WINDOWS_NL.md` section 8. The source archive is
**RELEASE CANDIDATE**, not CANONICAL_FROZEN until that actual Windows A999
acceptance returns PASS. All older frozen versions remain unchanged.


### RC2: verplichte voortgang en heartbeat

`run_all.cmd` start een onafhankelijk voortgangsproces. Per pipeline-fase en A999-backend
verschijnt direct een checkpoint; bij een lang lopende kernel verschijnt elke 15 s
een `[SST][HEARTBEAT] RUNNING`-regel, zonder verzonnen percentage.
Voor ruimtelijke/tijdelijke verfijningen gebruikt elke nieuwe falsifier
`sst_falsifier.progress.refinement(...)`. Zie `docs/PROGRESS_CONTRACT_v1.1.0_RC2_NL.md`.
`RUN_PROGRESS.jsonl` is een gehasht, blind-safe run-artifact.
**RC2 is nog niet CANONICAL_FROZEN:** na RC1 op de Windows-hardware moeten de RC2-suite en A999-integratie opnieuw draaien.
