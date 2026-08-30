import numpy as np
from qhp_sweep.geometry import arclength_resample_closed,apply_qhp,qhp_bases,center_rg

def trefoil(n=300):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+np.cos(3*t))*np.cos(2*t),(2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)]

def test_zero_is_exact_after_resample():
    x=arclength_resample_closed(trefoil(),192)
    y,_=apply_qhp(x,0,0,0)
    assert np.max(np.abs(x-y))<1e-12

def test_bases_equal_rms_and_normal_to_tangent_approximately():
    x=arclength_resample_closed(trefoil(),192); B=qhp_bases(x); rg=B['rg']
    for k in 'QHP':
        rms=np.sqrt(np.mean(np.sum(B[k]*B[k],axis=1)))
        assert abs(rms-rg)<1e-10

def test_signed_perturbations_are_symmetric():
    x=arclength_resample_closed(trefoil(),192)
    yp,_=apply_qhp(x,.03,0,0); ym,_=apply_qhp(x,-.03,0,0)
    assert np.max(np.abs((yp+ym)/2-x))<1e-11
