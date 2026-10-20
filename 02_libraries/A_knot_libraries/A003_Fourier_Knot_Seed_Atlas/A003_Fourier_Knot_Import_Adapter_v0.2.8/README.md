# A003 Fourier Knot Import Adapter v0.2.8.1 — Corrected G5 Qualification

**Scope:** F3 = T(2,3) and F4 = T(3,5), A003-v0.1.2 `uniform_t` XYZ, four resolutions **N=1200, 2400, 4800, 9600**, frozen primary projections **P0=(0.37,0.71)** and **P1=(0.63,1.17)** radians, direct and x-reflected mirror. **32** fresh corrected-provider observations are required for a complete run. The two new FULL resolutions contribute **16** new cases. A technical software screen is NOT knot, chirality or physical-vortex certification.

## v0.2.8.1 Windows test hotfix

The previous `run_all.cmd` could fail with `FileNotFoundError` on `outputs_g5c_braid_reference/g5c_braid_reference.json`: the old test incorrectly assumed a generated G5c output had already been produced. The self-contained regression now creates this report in a temporary directory using the unmodified production G5c calculation. Do **not** copy a JSON result by hand into the distribution to satisfy tests. The mathematics and live FULL G5Q gates are unchanged.

An activated command prompt `(.venv)` does not by itself verify the Python executable or provider; use the commands below to check them. The G5Q FULL provider result is independent of the test hotfix.

## Provenance and scientific controls

- This is a new sibling of v0.2.7. It does **not modify** historical adapters, v0.1.2 atlas, fixed geometry, previous negative stock-provider evidence or installed `site-packages`.
- Source atlas is reaudited against its 384 XYZ SHA-256 manifest `01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d` before any provider run.
- Historical v0.2.7 *live corrected* F3/F4 N1200/2400 observations are preserved as `tests/fixtures/g5_v027_live_corrected_lowres.json`, pinned by SHA-256. They are **not** new v0.2.8 measurements. Old stock F3 N2400/P1 determinant=1 remains historical FAIL.
- New G5Q2 tests old 16 corrected observations against the live baseline. New G5Q3 tests the 16 *new* N4800/9600 observations against the corresponding N2400 P0/P1 and mirror references. New G5Q4 tests full four-resolution Alexander polynomial stability, nonzero mirror-odd Vassiliev degree three, and reference algebra.
- G5Q6 independently reconstructs the **16** projected raw XYZ diagrams (2 knots x 4 mesh levels x 2 projections) and their Fox/Wirtinger determinant without pyKnotID. G5Q7 cross-checks the **32** pyKnotID determinant observations (including mirrors) against those 16 source-derived diagrams. Neither is complete topological classification.
- The v0.2.7 scoped angular crossing patch uses `abs(cross) < 1e-8*|u|*|v|`, forces Python helpers in `pyknotid==0.5.3` only, and restores original functions in `finally`. Provider version/source mismatch is **FATAL** (exit 4), never an inferred PASS.
- Framework source is externally pinned to `SST_Falsifier_Framework_v1.0.10`, `sst_falsifier/gates.py` SHA-256 `e5756c90a34d482e3dec7e0e9a22a131f7b8968f5de492832963f3063008a055`. The reviewed release status is `LOCAL_VALIDATED_CANDIDATE`; native v1.0.10 Windows validation not asserted.
- This package is **GateLedger integration**, NOT a generated blinded framework instance, CANONICAL_FROZEN release, or G9 reveal. G6 finite-core/Euler/PKLSA has no implementation and must remain `UNRESOLVED / NOT_EXECUTED`.

## Windows installation

Unzip beside `A003-v0.1.2` inside:

```text
SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\
  A003-v0.1.2\
  A003_Fourier_Knot_Import_Adapter_v0.2.7\
  A003_Fourier_Knot_Import_Adapter_v0.2.8.1\
```

Use the Workbench `.venv` and verify:

```bat
where python
python -c "import sys, importlib.metadata as m; print(sys.executable, m.version('pyknotid'))"
```

`pyknotid==0.5.3`, NumPy, and SymPy must be installed. No auto-install is performed. Optionally set `SST_FRAMEWORK_ROOT` to the exact v1.0.10 directory and `SST_ATLAS_ROOT` to the atlas. The stock v0.2.7 negative control is preserved and does not need to be recomputed at N4800/9600.

## Commands

```bat
run_all.cmd                       rem full atlas audit + adapter regression tests; no live corrected screen
run_all.cmd QUALIFY               rem live corrected 4-resolution provider campaign
run_g5_qualification.cmd          rem same as QUALIFY
run_all.cmd FULL                  rem audit + regressions, then full G5 qualifier
run_g5_qualification.cmd --skip-provider  rem provenance smoke only; expected exit 3
run_all.cmd DIAGNOSTIC            rem preserved v0.2.7 stock-vs-corrected historical diagnostic lane
```

The optional LaTeX compiler writes a PDF report; TeX/JSON outputs are always written. Runs are **non-overwriting** and uniquely timestamped in the sibling `A003_Fourier_Knot_Import_Adapter_v0.2.8.1-outputs/<run_id>/` directory.

Important output files:

- `GATE_LEDGER.json`: real v1.0.10 PASS / FAIL / UNRESOLVED / NOT_EXECUTED, recursive scientific qualifications.
- `QUALIFICATION_SUMMARY.json`: 32-case coverage and version/provenance.
- `g5_corrected_four_resolutions.json`: all corrected provider measurements, source/path/mirror details.
- `g5_qualification_comparisons.json`: 16 original + 16 new cases compared with pinned baseline.
- `g5q_independent_diagram_summary.json`: 16 source-only diagrams and SHA256 references; `raw_diagram_*.json` raw traces.
- `g5q_provider_diagram_comparison.json`: 32 provider-versus-raw-diagram determinant checks.
- `g5_historical_crossing_guard.json`: original 1200/2400 numerical tolerance control.
- `G5_QUALIFICATION_REPORT.tex`, optional `A003_v0.2.8.1_G5_QUALIFICATION_REPORT.pdf`.

### Exitcodes

| Code | Meaning |
|---|---|
| 0 | **PASS_INVARIANT_SCREEN_NOT_CERTIFIED**: all 32 live cases and independent checks passed; still not full knot certification |
| 2 | **FAIL_INVARIANT_SCREEN**: a recorded negative result; all available diagnostics still attempted |
| 3 | **UNRESOLVED**: provider absent, skipped or incomplete; never a manufactured PASS |
| 4 | **FATAL**: unexpected implementation error, incorrect framework pin, or altered atlas/fixture |

The 1e-8 angular tolerance is a candidate numerical fix verified for earlier low-resolution cases. Four-resolution live `pyknotid` results are **not contained** in this release and must be collected on the target Windows installation. Tests using a test-double remain explicitly non-scientific. No claimed Euler, PKLSA, finite-core self-confinement, or SST physics result follows from the screen.
