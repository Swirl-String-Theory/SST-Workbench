import numpy as np,pytest
from sst_falsifier.backend_contract import BackendResult,require_backend,BackendCertificationError,parity_gate

def test_strict_backend_rejects_python_fallback():
    r=BackendResult("cpp","python-fallback","float64","DEVELOPMENT",True)
    with pytest.raises(BackendCertificationError):require_backend(r,accepted_actual=["openmp","serial"],authority="CERTIFICATION")

def test_parity():
    p=parity_gate(np.array([1.,2.]),np.array([1.,2.]),1e-12);assert p["pass"] and p["relative_l2"]==0
