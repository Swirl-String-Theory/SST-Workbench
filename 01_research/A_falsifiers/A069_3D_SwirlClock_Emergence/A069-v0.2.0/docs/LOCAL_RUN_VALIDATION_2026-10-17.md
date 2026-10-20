# Local framework-v1.0.9 validation — 2026-10-17

- The v0.2.0 instance was generated with the original `tools/new_falsifier.py` fetched from the Google Drive v1.0.9 tree, and `.sst_framework_root` strictly references `SST_Falsifier_Framework_v1.0.9`.
- Selected necessary framework-v1.0.9 runtime files were individually fetched from the official Drive folder to assemble a *local test runtime*. **This local test runtime is not a complete, independently full-manifest-verified distribution of v1.0.9**, and its full 72 upstream framework tests were not reproduced here. For actual Windows qualification, install the full official v1.0.9 framework and run its `run_all.cmd ALL`.
- Scientific Python `unittest` regressions: **16/16 PASS** (9 inherited from v0.1.0, 7 new for columnar D2A).
- Official local v1.0.9 `FREEZE`: **PASS**; byte-exact preregistration SHA-256 `55dca109c8c31c48b64771afc2660754664adcb0b7943b111855206ba196354c`.
- Official local v1.0.9 `BASIC`: **PASS for the analytic-control methodology**; G0-G3 and G12-G14 PASS; G4-G7 NOT_APPLICABLE under minimal; G8-G11 UNRESOLVED.
- BLIND PDF generation: **PASS**, 5 pages.
- `REPORT_ONLY`: **PASS**, unique rerender without mutation to immutable evidence/final output manifests (before reveal-decision step).
- `REVEAL_IF_ALLOWED`: **WITHHELD** as required; current BASIC run is not eligible for reveal.
- Linux UTF-8 report-rendering compatibility issue: pdflatex/latexmk may emit 8-bit diagnostics that trigger a Python `UnicodeDecodeError` when the v1.0.9 report helper captures subprocess output as UTF-8. The source-v1.0.9 runtime was **not patched**. During local testing, an external shell shim converted only latexmk's terminal output from ISO-8859-1 to UTF-8 while leaving the TeX engine, report bytes and scientific source untouched. The first failed report run was preserved by the official non-overwrite archival mechanism. This should be fixed and retested in a subsequent framework version rather than altering frozen v1.0.9 in place.
- No C++/OpenMP, Windows MSVC, Intel Arc A770 SYCL/DD32, or physical PKLSA Euler provider was executed in this environment.
- A069 is a provisional catalog ID: final publication requires authoritative local registry validation.

The exact v0.1.0 control hash is fixed in `configs/BLIND_ANALYTIC_CONTROL_V020.json`. The old result is an internal analytic control, not an independent physical data source.
