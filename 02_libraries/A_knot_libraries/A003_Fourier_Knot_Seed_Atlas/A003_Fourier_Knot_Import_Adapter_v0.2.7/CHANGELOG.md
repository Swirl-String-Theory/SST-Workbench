# A003 Fourier Knot Import Adapter — changelog

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
