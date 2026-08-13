"""Post-hoc alpha benchmark for v0.4.

This is intentionally the only v0.4 module containing the numerical alpha target.
By default the function refuses to expose or compare the target unless the archived
blind summary reports H14 ready_for_alpha_unblinding=True.
"""
from __future__ import annotations
import math
from typing import Any
from .constants import TREFOIL_ROPELENGTH_HIRES

ALPHA_INV_BENCHMARK = 137.035999177


def alpha0_inverse(ropelength: float = TREFOIL_ROPELENGTH_HIRES) -> float:
    return (8.0*math.pi/3.0)*float(ropelength)


def benchmark_blind_summary(blind_summary: dict[str,Any], *, diagnostic_override: bool=False,
                            ropelength: float=TREFOIL_ROPELENGTH_HIRES,
                            alpha_inv: float=ALPHA_INV_BENCHMARK) -> dict[str,Any]:
    ready=bool(blind_summary.get("ready_for_alpha_unblinding",False))
    if not ready and not diagnostic_override:
        return {"benchmark_phase":"BLOCKED_BY_BLIND_RPO_FLOQUET_GATES","alpha_value_opened":False,
                "blind_verdict":blind_summary.get("verdict"),
                "reason":"No valid true Floquet phase may be compared with alpha before H14 passes."}
    tm=blind_summary.get("true_monodromy") or {}
    kr=tm.get("kelvin_readout") or {}
    if "true_floquet_phase_turns" not in kr:
        return {"benchmark_phase":"NO_TRUE_FLOQUET_PHASE_AVAILABLE","alpha_value_opened":bool(diagnostic_override),
                "blind_verdict":blind_summary.get("verdict")}
    h=float(kr["true_floquet_phase_turns"]); a0=alpha0_inverse(ropelength); target=float(alpha_inv-a0); pred=a0+h
    err=abs(h-target)/max(abs(target),1e-30)
    return {"benchmark_phase":"POST_HOC_ONLY_AFTER_H14_ARCHIVE" if ready else "DIAGNOSTIC_OVERRIDE_INVALID_ORBIT",
            "alpha_value_opened":True,"alpha_inverse_benchmark":float(alpha_inv),"alpha0_inverse":float(a0),
            "target_delta_abs":target,"true_floquet_phase_turns":h,"alpha_inverse_pred":float(pred),
            "error_in_target_correction_units":float(err),"within_10pct":bool(err<=.10),
            "verdict":"SURVIVES_V0_4_ALPHA_GATE" if ready and err<=.10 else "TRUE_FLOQUET_PHASE_MISSES_ALPHA"}
