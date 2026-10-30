# SST Falsifier Framework v1.0.10 — Full Diagnostic Execution

**Status:** `CANONICAL_FROZEN` — 2026-10-19, supported by 83/83 Windows regression, backend parity and instance smoke validation (overlay-installed RC2 provenance). Based on the byte-verified **v1.0.9 CANONICAL_FROZEN** package. The original v1.0.9 freeze remains intact.

## Core policy: `FAIL != STOP`

The scientific gate ledger now permits a completed **PASS / FAIL / UNRESOLVED** even if an upstream registered gate is negative, unresolved or not executed. The generated falsifier skeleton uses `ledger.run_evaluators({...})` to attempt **every enabled and available scientific evaluator**. `GateLedger.should_execute(id)` can be used in custom runners instead of `dependencies_pass(id)`.

**Two orthogonal outputs are mandatory:**

- **Observed outcome**: `status` (`PASS`, `FAIL`, `UNRESOLVED`, `NOT_RUN_PREREQUISITE`, etc.) and `execution_status` (`EXECUTED`, `NOT_EXECUTED`, `DISABLED`, `DEFERRED`). An unimplemented evaluator becomes `UNRESOLVED` + `NOT_EXECUTED`, never a fake measurement.
- **Scientific authority**: recursive `qualification` (`QUALIFIED`, `DIAGNOSTIC_ONLY`, `UNRESOLVED`, `BLOCKED_PREREQUISITE`, etc.), `blocked_by`, `prerequisite_statuses`, and `allows_dependent_claim`. An upstream qualified `FAIL` remains a valid negative finding but never satisfies a downstream positive prerequisite.

A gate can therefore have `status=PASS` with `qualification=DIAGNOSTIC_ONLY`. This DOES NOT promote a physical SST claim. An unsuccessful numerical condition does not automatically stop other independent computations.

`GateInputsUnavailable` is explicitly handled by `run_evaluators`, recording `NOT_RUN_PREREQUISITE`; only use this for genuinely missing data. Unexpected Python exceptions still abort an invalid run, never masquerade as scientific negative results. The framework's frozen protocol, blind integrity, source admissibility and commitment guards remain fail-closed.

**G9 reveal remains a separate operation**. The reveal preflight rejects diagnostic-only G3 `PASS`/`FAIL`, even if the raw status satisfies the reveal policy; it also continues to enforce required completed mode, signed hashes, no unresolved gates if so configured, and frozen commitments.

## Example in a new instance

```python
# Each evaluator returns a measured result, not an inferred prerequisite PASS.
evaluators = {
  "G1": lambda: {"status": "PASS", "reason": "source check"},
  "G2": lambda: {"status": "FAIL", "metrics": {"residual": 0.1}},
  "G3": lambda: {"status": "PASS", "metrics": {"statistic": 3.2}},
}
ledger.run_evaluators(evaluators)
# G3 was tested; status=PASS, qualification=DIAGNOSTIC_ONLY (blocked by G2).
```

Disabled profile gates are `NOT_APPLICABLE`; unimplemented gates are `UNRESOLVED` and `NOT_EXECUTED`. Older, historically frozen falsifier instances **are not silently rewritten** and preserve their original framework pins. Port a custom pipeline to `run_evaluators` or `should_execute` to obtain full-diagnostic behavior.

## Required local checks before canonical promotion (Windows / Intel Arc A770)

```bat
cd /d C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10
run_all.cmd ALL
run_all.cmd DD32
.venv\Scripts\python.exe tools\smoke_non_short_circuit.py
.venv\Scripts\python.exe tools\smoke_run_identity.py
```

The last two smoke runs create temporary instances and should produce their own PDF reports when LaTeX is available. Verify `build/BACKEND_SELFTEST.json` with `overall_pass=true`, plus non-short-circuit smoke PASS and preserved run-ID reports. Record independent SHA-256 evidence outside the immutable source ZIP; do not rewrite this candidate in place. **Only then** produce the external canonical freeze decision and rename the unchanged ZIP to `CANONICAL_FROZEN`.

The tests are software qualification, **not** proof of real Euler/PKLSA/SST physics or native whole-solver parity. DD32 remains `SCREENING_ONLY`.
