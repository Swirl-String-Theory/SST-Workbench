import numpy as np
from e012_dynamic.tracking import track_from_finest, select_fine_anchored_branch, subspace_overlap

def test_phase_invariant_overlap():
    a=np.array([1+0j,0,0,0])
    b=np.exp(1j*1.234)*a
    assert abs(subspace_overlap(a,b)-1.0)<1e-12

def test_overlap_tracking_survives_eigenvalue_order_swap():
    # Columns encode identities; eigenvalue ordering swaps between levels.
    eye=np.eye(4,dtype=complex)
    lev1={'label':40,'eigenvalues':np.array([1j,2j,3j,4j]),'eigenvectors':eye}
    vals2=np.array([2.02j,1.01j,4.01j,2.98j])
    vec2=eye[:,[1,0,3,2]]
    lev2={'label':56,'eigenvalues':vals2,'eigenvectors':vec2}
    tr=track_from_finest([lev1,lev2],rel_tol=0.05,overlap_min=0.95,eigenvalue_weight=0.5,overlap_weight=0.5)
    b=select_fine_anchored_branch(tr,1)  # fine index 1 is the ~1j identity
    assert b['persistent']
    assert abs(b['points'][0]['lambda'].imag-1.0)<1e-12
    assert abs(b['points'][1]['lambda'].imag-1.01)<1e-12
