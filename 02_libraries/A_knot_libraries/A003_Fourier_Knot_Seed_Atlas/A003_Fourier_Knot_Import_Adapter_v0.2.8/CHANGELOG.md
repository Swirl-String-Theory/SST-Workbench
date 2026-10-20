# A003 Fourier Knot Import Adapter — changelog

## v0.2.8.1 maintenance hotfix — 2026-10-20

- Corrects a **test fixture dependency**, not an invariant: `test_g5c_no_false_certification` now runs the shipped production `g5c_braid_reference.main()` with the verified A003 atlas into a temporary directory. It no longer expects the non-shipped `outputs_g5c_braid_reference/g5c_braid_reference.json` to exist before `run_all.cmd`.
- G5c still requires 30/30 algebraic braid references, validates the full 384-export atlas, and MUST keep topology/chirality certification false. No generated runtime evidence is silently bundled.
- Output paths and displayed adapter versions are updated to `v0.2.8.1`; no edits to knot XYZ, G5 mathematical thresholds, pyKnotID crossing patch, framework source pin, historical negative G5 data, or G6.
- `run_all.cmd` is a geometry audit and test suite; `run_all.cmd QUALIFY` still requires the installed `pyknotid` provider and actual pinned Framework v1.0.10, and results are not inferred from this hotfix.

## v0.2.8 — Corrected G5 Qualification — 2026-10-19

- New sibling release; **no modifications** to v0.2.7, the A003-v0.1.2 atlas or installed pyKnotID.
- Added full **N=1200/2400/4800/9600** F3/F4 corrected crossing provider screen with 32 frozen projection/mirror cases.
- Added a SHA-256-pinned historical user-live v0.2.7 corrected-provider fixture as the N=1200/2400 baseline; all 16 new FULL cases are checked independently against it.
- Added v1.0.10 `GateLedger` G5Q0-Q7 including independent raw crossing diagram determinants (16 new source-derived cases) and provider/diagram determinant parity (32 cases); G6 remains NOT EXECUTED.
- Negative and incomplete provider results fail closed without short-circuiting independent diagnostics; offline/mock controls are never promoted to provider evidence.
- Unique output folder per run; TeX/optional PDF, comparisons and raw crossing traces; explicit `run_all.cmd QUALIFY` / `FULL` and `run_g5_qualification.cmd`.
- Historical stock N2400/P1 FAIL is unchanged. Four-level live pyKnotID provider run awaits Windows target execution.

## v0.2.7 — Crossing Tolerance Correction — 2026-10-19

- Preserves v0.2.6's G0–G6 architecture, source hashes, historical negative F3 provider evidence, diagnostic non-short-circuit and Framework v1.0.10 source hash pin.
- New **scoped** `pyknotid 0.5.3` Python helper control replaces the unnormalised `abs(cross)<1e-5` with dimensionless `abs(cross) < 1e-8*norm(u)*norm(v)` while maintaining endpoint exclusion. No source package/site-packages edits, fully restored after run/exception.
- Explicitly force the *Python* crossing helper in both stock and corrected control, to avoid Cython-vs-Python confounds; refuse unknown provider releases/source signatures.
- New G5g corrected extended invariants, G5h paired stock/fixed crossing regression and G5i independent frozen F3 threshold diagnostic. G5g/h dependent on G5a; a corrected PASS is `DIAGNOSTIC_ONLY` when stock G5a FAIL.
- Historical replay never claims corrected-provider observation. `GATE_LEDGER.json` maintains raw `status`, `execution_status` and recursive `qualification` with all later evaluators attempted.
- Separate v0.2.7 output directories, PDF/TeX/JSON evidence. Framework metadata read live rather than claiming canonical status.
- Development static/fake-provider unit checks, source-backed v1.0.10 GateLedger and F3 numerical geometry comparison. Corrected real `pyknotid` runtime pending target machine.

## v0.2.6

Non-short-circuit diagnostic evaluator integration, G5e and G5f independent crossing traces, historical provider-vs-diagram disagreement retained. See prior immutable v0.2.6 release for its original sources and reports.
