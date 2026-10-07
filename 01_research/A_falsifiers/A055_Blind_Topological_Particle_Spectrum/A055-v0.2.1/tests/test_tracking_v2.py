import numpy as np
from a055_spectrum.tracking import subspace_overlap,track_from_finest
def test_overlap_phase_invariant():
    v=np.array([1+1j,2-1j]); assert abs(subspace_overlap(v,np.exp(1j*.7)*v)-1)<1e-12
def test_tracking_simple():
    V=np.eye(2,dtype=complex)
    levels=[{"label":20,"eigenvalues":np.array([1j,2j]),"eigenvectors":V},
            {"label":40,"eigenvalues":np.array([1.02j,2.01j]),"eigenvectors":V}]
    t=track_from_finest(levels,.1,.8)
    assert t["persistent_count"]==2
