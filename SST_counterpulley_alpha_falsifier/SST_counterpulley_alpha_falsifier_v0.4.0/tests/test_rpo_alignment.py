import numpy as np
from sst_counterpulley.core import prepare_centerline
from sst_counterpulley.geometry import make_counter_channels, rigid_rotation_matrix
from sst_counterpulley.orbit import best_relative_alignment


def test_rpo_alignment_removes_se3_and_common_shift():
    c,m=prepare_centerline(n=24)
    D=m['D_metadata']
    p,q,_,_=make_counter_channels(c,0.5*D)
    ref=np.stack((p,q))
    R=rigid_rotation_matrix(); t=np.array([0.2,-0.4,0.1])
    mov=np.roll(ref,7,axis=1)@R.T+t
    a=best_relative_alignment(ref,mov,D=D)
    assert a['rms_over_D'] < 1e-11
    assert abs(a['det_rotation']-1.0) < 1e-12
