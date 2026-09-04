from pathlib import Path
import numpy as np
from sst_counterpulley.core import prepare_centerline
from sst_counterpulley.geometry import make_counter_channels
from sst_counterpulley.rpo_solver import fractional_channel_relabel, transverse_shape_basis, newton_krylov_multiple_shooting
import sst_counterpulley.rpo_solver as solver

def test_integer_longitudinal_relabel_is_exact_gauge():
    c,m=prepare_centerline(n=20); D=m['D_metadata']
    p,q,_,_=make_counter_channels(c,.5*D); x=np.stack((p,q))
    y=fractional_channel_relabel(x,1.0,channel=1)
    assert np.linalg.norm(y-x) < 1e-12

def test_transverse_basis_is_orthonormal():
    c,_=prepare_centerline(n=20); B=transverse_shape_basis(c,max_cols=6)
    assert B.shape==(120,6)
    assert np.linalg.norm(B.T@B-np.eye(6)) < 1e-10

def test_solver_module_is_alpha_blind():
    text=Path(solver.__file__).read_text(encoding='utf-8')
    assert '137.035' not in text
    assert 'ALPHA_INV_BENCHMARK' not in text

def test_newton_krylov_smoke_returns_full_state_metrics():
    c,m=prepare_centerline(n=8); D=m['D_metadata']; p,q,_,_=make_counter_channels(c,.4*D); x=np.stack((p,q))
    r=newton_krylov_multiple_shooting(c,D=D,state0=x,seed_period_hat=.12,eps_over_D=.1,
        segments=2,basis_cols=2,dt_hat=.02,max_newton=1,force_python=True,skip_build=True)
    rr=r['result']
    assert np.isfinite(rr['final_projected_residual'])
    assert np.isfinite(rr['recurrence_rms_over_D'])
    assert 'endpoint_vectorfield_error' in rr
