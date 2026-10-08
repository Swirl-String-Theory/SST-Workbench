from __future__ import annotations
from dataclasses import dataclass,asdict,field
from typing import Any,Iterable
import numpy as np

class BackendCertificationError(RuntimeError): pass

@dataclass(frozen=True)
class BackendResult:
    requested_backend: str
    actual_backend: str
    precision: str
    authority: str
    ok: bool
    metrics: dict[str,Any]=field(default_factory=dict)
    source_sha256: str|None=None
    build_fingerprint_sha256: str|None=None
    device_name: str|None=None
    def to_dict(self): return asdict(self)


def require_backend(result: BackendResult, *, accepted_actual: Iterable[str], authority: str|None=None, precision: str|None=None) -> BackendResult:
    accepted=set(accepted_actual)
    if not result.ok: raise BackendCertificationError(f"backend reported failure: {result}")
    if result.actual_backend not in accepted:
        raise BackendCertificationError(f"requested {result.requested_backend}, actual {result.actual_backend}; accepted={sorted(accepted)}")
    if authority is not None and result.authority!=authority:
        raise BackendCertificationError(f"authority mismatch: actual={result.authority} required={authority}")
    if precision is not None and result.precision!=precision:
        raise BackendCertificationError(f"precision mismatch: actual={result.precision} required={precision}")
    return result


def relative_l2(candidate, reference, eps: float=1e-30) -> float:
    c=np.asarray(candidate,dtype=float); r=np.asarray(reference,dtype=float)
    return float(np.linalg.norm(c-r)/max(float(np.linalg.norm(r)),eps))


def parity_gate(candidate, reference, tolerance: float) -> dict[str,Any]:
    rel=relative_l2(candidate,reference)
    return {"relative_l2":rel,"tolerance":float(tolerance),"pass":bool(rel<=tolerance),"reference_norm":float(np.linalg.norm(reference)),"candidate_norm":float(np.linalg.norm(candidate))}
