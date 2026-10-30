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
from sst_falsifier import progress


def run_scientific_pipeline(root: Path, cfg: dict[str,Any], ledger, mode: str) -> dict[str,Any]:
    # G0 is allowed to PASS only because runner already verified the frozen protocol.
    ledger.record("G0","PASS",metrics={"mode":mode},reason="Frozen protocol verified by framework before pipeline entry.")

    # Non-short-circuit default: register a zero-argument evaluator for EVERY
    # gate you can calculate. Each callable runs even after any upstream FAIL.
    # Example: "G2": lambda: {"status": "PASS", "metrics": {"relative_error": 1e-8}}
    # Missing implementations are UNRESOLVED, not silently marked PASS/FAIL.
    # Raise GateInputsUnavailable ONLY when a measurement physically requires
    # missing data, not merely because an earlier scientific criterion failed.
    # For real, long-running spatial and temporal convergence studies:
    # for i, N in enumerate((128, 256, 512), start=1):
    #     with progress.refinement('spatial',level=i,total=3,resolution=N):
    #         run_fixed_final_time_spatial_case(N)
    # for i, dt in enumerate((0.01, 0.005, 0.0025), start=1):
    #     with progress.refinement('temporal',level=i,total=3,dt=dt,final_time=1.0):
    #         run_fixed_final_time_temporal_case(dt)
    # These contexts report progress even if a given level takes several minutes.
    evaluators = {}  # add real tests; no evaluator means NOT_EXECUTED / UNRESOLVED
    ledger.run_evaluators(evaluators)
    return {
        "schema":"SST-BACKEND-MANIFEST-2",
        "note":"Fresh instance has no implemented physical tests; all non-evaluated gates remain UNRESOLVED, even after upstream FAIL.",
        "python_reference":{"actual_backend":"python-numpy-fp64","precision":"float64","authority":"REFERENCE"}
    }
