from sst_counterpulley.core import prepare_centerline
from sst_counterpulley.dynamics import compute_dynamic_blind, turn_wrap

def test_eigenclock_internal_phase_consistency():
    c,m=prepare_centerline(n=64)
    r=compute_dynamic_blind(c,D=m['D_metadata'],force_python=True,skip_build=True)
    assert r.gram_error_fro<1e-12
    assert r.phase_internal_consistency_turns<1e-12

def test_basis_gauge_invariance():
    c,m=prepare_centerline(n=64); D=m['D_metadata']
    a=compute_dynamic_blind(c,D=D,basis_phase=0.0,force_python=True,skip_build=True)
    b=compute_dynamic_blind(c,D=D,basis_phase=.73,force_python=True,skip_build=True)
    assert abs(turn_wrap(a.floquet_phase_signed_turns-b.floquet_phase_signed_turns))<2e-6

def test_circulation_reversal_covariance():
    c,m=prepare_centerline(n=64); D=m['D_metadata']
    a=compute_dynamic_blind(c,D=D,force_python=True,skip_build=True)
    b=compute_dynamic_blind(c,D=D,gamma_plus=-1,gamma_minus=1,force_python=True,skip_build=True)
    assert abs(turn_wrap(a.floquet_phase_signed_turns+b.floquet_phase_signed_turns))<2e-6
    assert abs(a.floquet_phase_scalar_defect_turns-b.floquet_phase_scalar_defect_turns)<2e-6
