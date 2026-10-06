from a052_lfpdcf.core import centered_group_velocity, log_slope

def test_group_velocity_linear():
    k=[1.,2.,3.,4.]; w=[2.,4.,6.,8.]
    assert centered_group_velocity(k,w)==[2.,2.]

def test_log_slope():
    f=log_slope([1,2,4],[1,4,16])
    assert abs(f['slope']-2)<1e-12 and f['r2']>0.999999
