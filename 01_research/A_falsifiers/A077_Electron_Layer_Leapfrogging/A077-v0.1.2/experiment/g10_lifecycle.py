"""A077-specific pre-backend gate scheduler for SST Framework 1.1.0.

Framework runner.py owns G10 after run_auto_matrix(); the generic
GateLedger.run_evaluators() would otherwise pre-fill the missing G10 with
UNRESOLVED and prevent the official numeric assessment. This adapter uses the
same GateLedger.record and GateInputsUnavailable semantics, explicitly leaving
G10 unrecorded until the unchanged Framework runner executes its own evaluator.

Never create a G10 PASS here, and never alter _sst_runtime or its hashes.
"""
from __future__ import annotations
from typing import Any, Callable
from sst_falsifier.gates import GateError, GateInputsUnavailable, TERMINAL


def run_pre_backend_evaluators(ledger, evaluators: dict[str, Callable[[], dict[str, Any]]]) -> None:
    if 'G10' not in ledger.defs:
        raise GateError('A077 requires a preregistered Framework G10 definition')
    if ledger.status('G10') is not None:
        raise GateError('G10 must not be evaluated before the framework backend matrix')
    for gid, definition in ledger.defs.items():
        if gid in ('G9', 'G10') or ledger.status(gid) is not None:
            continue
        if not definition.enabled:
            ledger.record(gid, 'NOT_APPLICABLE', reason='Disabled by framework profile')
            continue
        evaluator = evaluators.get(gid)
        if evaluator is None:
            ledger.record(gid, 'UNRESOLVED',
                          reason='No scientific evaluator implemented for this gate; not executed',
                          execution_status='NOT_EXECUTED')
            continue
        try:
            result = evaluator()
        except GateInputsUnavailable as exc:
            ledger.record(gid, 'NOT_RUN_PREREQUISITE',
                          reason=f'Required scientific inputs unavailable: {exc}')
            continue
        if not isinstance(result, dict) or result.get('status') not in TERMINAL:
            raise GateError(f'evaluator {gid} must return a mapping with a valid status')
        if result['status'] in {'DEFERRED', 'NOT_APPLICABLE'}:
            raise GateError(f'enabled blind evaluator {gid} cannot return {result["status"]}')
        ledger.record(gid, result['status'], metrics=result.get('metrics'),
                      reason=result.get('reason', ''), execution_status='EXECUTED',
                      requested_backend=result.get('requested_backend'),
                      actual_backend=result.get('actual_backend'),
                      authority=result.get('authority'))
    assert ledger.status('G10') is None, 'G10 was unexpectedly consumed before Framework assessment'
