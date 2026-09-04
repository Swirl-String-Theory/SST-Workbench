from sst_counterpulley.core import prepare_centerline
from sst_counterpulley.dynamics import compute_dynamic_blind

def test_current_counterpulley_is_not_relative_equilibrium():
    c,m=prepare_centerline(n=96)
    r=compute_dynamic_blind(c,D=m['D_metadata'],force_python=True,skip_build=True)
    assert r.relative_equilibrium_residual>0.8
