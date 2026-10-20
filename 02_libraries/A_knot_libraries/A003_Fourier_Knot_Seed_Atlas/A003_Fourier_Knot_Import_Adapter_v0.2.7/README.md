# A003 Fourier Knot Import Adapter v0.2.7 — Crossing Tolerance Correction

**Release type:** separate, versioned diagnostic adapter. **Do not modify** A003-v0.1.2, v0.2.6, any historical outputs, or site-packages. Framework 1.0.10 is an *external exact-pin dependency*, not bundled.

## Root cause and limited correction

`pyknotid 0.5.3`, Python implementation, `spacecurves.helpers.do_vectors_intersect` rejects a projected segment pair if its **unnormalized** 2D cross product is less than `1e-5`. The cutoff is not invariant when N increases and the segment lengths decrease. A003's frozen `fibonacci_torus_F3`, P1:

| Case | Crossing pair | abs(cross) | abs(sin(angle)) | Stock 1e-5 | Angular 1e-8 |
|---|---|---:|---:|---|---|
| N1200 | (65,1041) | 3.921309974e-5 | .26875780 | accept | accept |
| N2400 | (131,2083) | 9.692496001e-6 | .26573346 | **reject** | accept |

`g5_crossing_tolerance_v027.py` switches the orientation guard to `abs(cross) < 1e-8 * length_u * length_v`, equivalent to `abs(sin(angle)) < 1e-8`. It retains the strict `0<t,u<1` intersection requirement. This is a **numerical candidate** tolerance, not an independently certified general-purpose robust predicate for all knot resolutions/coordinates.

`scoped_pyknotid_crossing_fix()` temporarily patches the **Python** helper and forces `SpaceCurve.raw_crossings(..., try_cython=False)` for the interval of the corrected provider run. It restores both functions in `finally`, including when an exception is thrown, and refuses unsupported `pyknotid` versions or an unexpected helper source. The *stock control* uses the same Python backend, but the original fixed tolerance, to avoid conflating Cython-vs-Python effects. **No package install tree is modified.** The context operates on process-wide Python objects; never run concurrent provider operations in that Python process.

## Framework and scientific-status policy

Framework source: `06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10`; imported `sst_falsifier.gates.GateLedger.run_evaluators` after version and SHA-256 pin verification (`FRAMEWORK_PIN.json`). The source reviewed 2026-10-19 was `LOCAL_VALIDATED_CANDIDATE`, not canonical; the adapter always records metadata observed on the user's target machine. This is **GateLedger integration**, not a generated blind SST falsifier instance, framework reveal, or SYCL/Arc GPU benchmark.

- **G0–G3** verify source manifest, 384 XYZ hashes and sampling geometry.
- **G4** is the same conditional dimensional `a_star=0.05` scale hypothesis.
- **G5a–G5d (STOCK)** preserve the unmodified original provider screen (F3 N2400/P1 historically FAIL). It must never be overwritten by a corrected control.
- **G5e** independently reconstructs crossings/Gauss/Fox-Wirtinger determinant, with G5a FAIL allowed.
- **G5f** compares *stock* provider and independent determinant; historical disagreement is preserved.
- **G5g (NEW)** recomputes bounded F3/F4 with the scoped corrected helper; a PASS means only that the tested multi-invariant screen now matches. With G5a FAIL, the framework assigns `DIAGNOSTIC_ONLY`.
- **G5h (NEW)** records all 16 F3/F4 primary/mirror case pairs of stock vs corrected. A PASS requires the frozen F3 N2400/P1 determinant change **1 → 3** and `v3 → -1`, while the remaining primary cases are stable. Missing data, no reproduced original failure, or test doubles must **not** count as a PASS.
- **G5i (NEW)** provider-independent first-bad-crossing cutoff diagnosis using hashed F3 XYZ; `PASS / DIAGNOSTIC_ONLY` does **not** imply the real pyknotid repair worked.
- **G6** remains `UNRESOLVED / NOT_EXECUTED` (no Euler/PKLSA).

Scientific FAIL != process STOP. Failed gates persist in `GATE_LEDGER.json`, while following diagnostic evaluators still run. A failed science gate returns exit **2** even when every diagnostic artifact and PDF was produced. A source-integrity failure or unexpected programming exception is fatal (**4**). New run directories are create-only and unique.

## Install (Windows)

Unpack beside the atlas:

```text
C:\workspace\projects\SST-Workbench\02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\
  A003-v0.1.2\
  A003_Fourier_Knot_Import_Adapter_v0.2.6\
  A003_Fourier_Knot_Import_Adapter_v0.2.7\
```

Use the SST-Workbench `.venv`, and ensure `pyknotid==0.5.3`, NumPy and SymPy are installed. The following *is not* a framework installation:

```bat
python -c "import sys,importlib.metadata as m; print(sys.executable); print(m.version('pyknotid'))"
```

If framework discovery fails, set `SST_FRAMEWORK_ROOT` to the **exact** v1.0.10 folder. Its `sst_falsifier/gates.py` hash must match `FRAMEWORK_PIN.json`; no fallback to another framework is permitted.

### Execute

```bat
run_all.cmd                          rem 384 XYZ audit + unit tests, no extended provider by default
run_g5_diagnostic_replay.cmd         rem historical stock FAIL, NO corrected-provider evidence; exit 2
run_g5_diagnostic.cmd                rem LIVE stock then LIVE corrected, both Python backend
```

The live entrypoint `run_g5_diagnostic.cmd` is the main v0.2.7 validation. You can also use `run_all.cmd DIAGNOSTIC`. Avoid `run_g5_projection_robustness.cmd` for these new gates; it is preserved only as historical/legacy interface.

For a deliberately uncorrected control: `run_g5_diagnostic.cmd --skip-corrected`. For a geometry-only smoke: `run_g5_diagnostic_smoke.cmd`. Replay is *not* evidence that the correction works.

### Inspect outputs

Outputs appear **outside the adapter** in a unique folder:

```text
..\A003_Fourier_Knot_Import_Adapter_v0.2.7-outputs\<run_id>\
  GATE_LEDGER.json
  DIAGNOSTIC_RUN_SUMMARY.json
  g5_provider_observations.json                (stock)
  g5_corrected_provider_observations.json      (patched control + patch metadata)
  g5h_stock_corrected_comparison.json          (all paired cases)
  g5i_numeric_guard_evidence.json              (first-bad-crossing threshold)
  g5e_raw_crossing_summary.json
  g5f_provider_diagram_comparison.json
  raw_crossings_*                              (independent traces)
  DIAGNOSTIC_REPORT.md
  DIAGNOSTIC_REPORT.tex
  A003_v0.2.7_DIAGNOSTIC_REPORT.pdf            (when pdflatex is available)
```

Expected frozen stock negative: `G5a FAIL`, `G5f FAIL`. **A corrected G5g PASS is only a prospective hypothesis** until the actual target machine produces and archives the live evidence. A corrected `G5h PASS` further confirms the exact local provider discrepancy; neither constitutes complete knot-identity/chirality certification.

## Development qualification boundary

Development tests checked the real atlas v0.1.2 geometry, hash-pinned `GateLedger` source from v1.0.10, controlled injection of stock/fixed observations, the historical negative replay, and reversible provider monkeypatch semantics. `pyknotid` was **not installed in this build container**. Hence its real complete Alexander/Vassiliev run with the corrected predicate has **not** been validated here. Windows CMD execution and target framework/gpu validation require the user's machine.
