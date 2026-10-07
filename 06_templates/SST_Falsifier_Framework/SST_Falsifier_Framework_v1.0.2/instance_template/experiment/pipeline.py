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

    # IMPORTANT: replace these UNRESOLVED records with experiment-specific tests.
    # They deliberately prevent a fresh instance from producing a false scientific PASS.
    ledger.record("G1","UNRESOLVED",reason="Implement source-admissibility checks in experiment/pipeline.py.")
    for gid in ("G2","G3","G4","G5","G6","G7","G8"):
        if not ledger.defs[gid].enabled:
            ledger.record(gid,"NOT_APPLICABLE",reason="Disabled by selected framework profile.")
        else:
            ledger.skip_due_prerequisite(gid)
    return {
        "schema":"SST-BACKEND-MANIFEST-2",
        "note":"Fresh instance intentionally remains UNRESOLVED until scientific/backend gates are implemented.",
        "python_reference":{"actual_backend":"python-numpy-fp64","precision":"float64","authority":"REFERENCE"}
    }
