# A003 Fourier Knot Import Adapter v0.2.6

**Purpose:** G5 projection/diagram diagnostics with **non-short-circuit** science-gate execution using the actual external `SST_Falsifier_Framework v1.0.10` `GateLedger` API. This is a separate versioned adapter; A003-v0.1.2 XYZ geometry and historical v0.2.5 outputs are not modified.

## Status and scientific limits

- Geometry: G0–G3 unchanged; all 384 hashed XYZ assets / 48 seeds.
- G4: `PASS_DIMENSIONAL_HYPOTHESIS_ONLY`, with **assumed** `a_star=0.05` coordinate units and `r_c=1.40897017e-15 m`, not an inferred finite-core radius.
- G5a: full Alexander polynomial from optional installed pyknotid / SymPy for bounded test cases.
- G5b: `v3` mirror behavior; `v3=0` is **not** chirality evidence.
- G5c: algebraic torus braid/Burau reference *from source-declared p,q only*.
- G5d: frozen primary two projections x two sampling resolutions; supplementary projection probes do **not** rescue failed primary gates.
- G5e **NEW**: independent raw 2D polygon crossings, depth ordering, Gauss events, integer Wirtinger/Fox matrix at `t=-1`. This is only an **Alexander determinant**, not the full polynomial or knot classification.
- G5f **NEW**: cross-compare provider `|Delta(-1)|` against the independent G5e coloring determinant. The historic F3 failure shows provider=1 vs independent=3 at N=2400/P1.
- G6 / PKLSA/Euler: **NOT EXECUTED**.

Framework **1.0.10 status in Google Drive on 2026-10-19: `LOCAL_VALIDATED_CANDIDATE`**, not canonical. Hardware and target-system certification of v1.0.10 remain pending. `FRAMEWORK_PIN.json` records the expected external version and a SHA-256 of its actual GateLedger source.

**Boundary:** This adapter integrates **the v1.0.10 GateLedger**, but it is *not* an auto-generated complete SST Falsifier Framework instance. It does not execute the framework's blind protocol, reveal/G9, C++/SYCL/DD32 backends, or a certified experiment. A003 produces its own diagnostic PDF through pdflatex when available. It does not label that PDF as a reveal-authoritative framework report.

## Install location (Windows)

```text
C:\workspace\projects\SST-Workbench\
  02_libraries\A_knot_libraries\A003_Fourier_Knot_Seed_Atlas\
    A003-v0.1.2\                  <- unchanged atlas
    A003_Fourier_Knot_Import_Adapter_v0.2.5\  <- unchanged older code
    A003_Fourier_Knot_Import_Adapter_v0.2.6\  <- unpack new ZIP here
  06_templates\SST_Falsifier_Framework\
    SST_Falsifier_Framework_v1.0.10\          <- external dependency
```

Use your SST-Workbench `.venv`, which already has `pyknotid 0.5.3`, NumPy and SymPy. Install missing dependencies yourself with `python -m pip install -r requirements.txt`; do **not** reinstall or replace the frozen framework through this adapter.

### First run — historical fail replay (fast)

```bat
run_g5_diagnostic_replay.cmd
```

Reuses the actual v0.2.5 `extended_g5_screen` response previously supplied by the user (provenance inside `tests/fixtures/g5_v025_extended_replay.json`). This is **replay**, *not new evidence*. It must produce:

```text
G5a FAIL             (primary provider result, from historical replay)
G5e PASS             DIAGNOSTIC_ONLY (independent raw geometry)
G5f FAIL             DIAGNOSTIC_ONLY (provider vs diagram)
G5d FAIL             DIAGNOSTIC_ONLY (primary projections disagree)
G6  UNRESOLVED       NOT_EXECUTED (physically NOT_RUN)
exit code 2          expected scientific FAIL; diagnostic nevertheless complete
```

### Second run — fresh pyknotid computation (slower)

```bat
run_g5_diagnostic.cmd
```

Or `run_all.cmd DIAGNOSTIC`. This runs the original bounded G5a-d primary test and additional diagnostic cases for F3/F4. Do not use `run_g5_projection_robustness.cmd` if you expect the new framework ledger; it is the legacy v0.2.5 entrypoint. The frozen G5 crossing complexity limit is 12; higher Fibonacci torus knots remain `COST_GUARD_UNRESOLVED`.

### Optional geometry-only smoke

```bat
run_g5_diagnostic_smoke.cmd
```

G5 provider unexecuted (`UNRESOLVED`); confirms source geometry and G5e, not G5a-d. Exit code 3 is expected.

### Override framework location

The `.cmd` script automatically detects:

```text
<WORKBENCH>\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10
```

You may override only by pointing to **that exact version**:

```bat
set "SST_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
run_g5_diagnostic.cmd
```

If the exact framework version, source hash, or API is missing or different, execution aborts with exit code **4**. Scientific FAIL is **not** allowed to skip independent diagnostic gates. A source/manifest integrity failure is different: that aborts without allowing invalid evidence.

## Output contract

Each execution creates a **unique immutable run directory** under

```text
..\A003_Fourier_Knot_Import_Adapter_v0.2.6-outputs\<timestamp>_<nonce>\
```

The directory contains `GATE_LEDGER.json` generated from the actual framework `GateLedger.to_dict()`; `DIAGNOSTIC_RUN_SUMMARY.json`; `g5_provider_observations.json`; `g5c_references.json`; eight `raw_crossings_{F3,F4}_N{1200,2400}_P{0,1}.json`; `g5e_raw_crossing_summary.json`; `g5f_provider_diagram_comparison.json`; `DIAGNOSTIC_REPORT.md`, `DIAGNOSTIC_REPORT.tex`, optional `A003_v0.2.6_DIAGNOSTIC_REPORT.pdf`, and `PDF_RENDER.json`.

The framework ledger separates measured `status`, `execution_status`, `qualification`, `blocked_by` and `allows_dependent_claim`. A qualified `G5a=FAIL` remains negative; `G5e=PASS` is **DIAGNOSTIC_ONLY**, not authority for topology/chirality claims. `G9` reveal is unavailable.

Output folders are create-only with random run IDs; original A003 and v0.2.5 files are never overwritten. `run_all.cmd` still executes the unchanged basic A003 audit and regression checks when called with no arguments.

## Development validation

In the packaging environment, the real v1.0.10 `gates.py` and `util.py` were downloaded from the user's connected Drive and used only in a **separate test fixture**; the framework is **not** bundled. With that authentic source, **58/58 Python tests passed** including the historical replay and persisted diagnostic PDF. The 384/384 geometric audit remains intact. The fresh `pyknotid 0.5.3` calculation is **not independently rerun on Windows** here; run it on the target machine.

References: Kauffman, *Fourier Knots*, arXiv:q-alg/9711013; Alexander (1928), *Topological Invariants of Knots and Links*.
