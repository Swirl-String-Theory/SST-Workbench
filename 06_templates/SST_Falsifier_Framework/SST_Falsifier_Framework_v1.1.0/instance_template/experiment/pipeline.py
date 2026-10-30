"""Scientific pipeline skeleton.

Replace the example decisions with the actual falsifier logic. The framework owns ordering,
provenance and backend semantics; this module owns the science.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np
from sst_falsifier.backend_contract import parity_gate,require_backend
from sst_falsifier.backends import python_ref


def run_scientific_pipeline(root: Path, cfg: dict[str,Any], ledger, mode: str) -> dict[str,Any]:
    # G0 is allowed to PASS only because runner already verified the frozen protocol.
    ledger.record("G0","PASS",metrics={"mode":mode},reason="Frozen protocol verified by framework before pipeline entry.")

    # Non-short-circuit default: register a zero-argument evaluator for EVERY
    # gate you can calculate. Each callable runs even after any upstream FAIL.
    # Example: "G2": lambda: {"status": "PASS", "metrics": {"relative_error": 1e-8}}
    # Missing implementations are UNRESOLVED, not silently marked PASS/FAIL.
    # Raise GateInputsUnavailable ONLY when a measurement physically requires
    # missing data, not merely because an earlier scientific criterion failed.
    evaluators = {}  # add real tests; no evaluator means NOT_EXECUTED / UNRESOLVED
    ledger.run_evaluators(evaluators)
    return {
        "schema":"SST-BACKEND-MANIFEST-2",
        "note":"Fresh instance has no implemented physical tests; all non-evaluated gates remain UNRESOLVED, even after upstream FAIL.",
        "python_reference":{"actual_backend":"python-numpy-fp64","precision":"float64","authority":"REFERENCE"}
    }
