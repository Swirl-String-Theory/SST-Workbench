import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phaseclock import demo,compare_two
import numpy as np

def test_positive_synthetic():
    assert demo()['positive_two_shape_signals']['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'

def test_rigid_body_null():
    assert demo()['negative_rigid_rotation_shape_invariants']['G3_phase_reproducibility']=='SCREEN_FAIL'

def test_beating_null():
    assert demo()['negative_beating']['G3_phase_reproducibility']=='SCREEN_FAIL'

def test_nonmonotone_rejected():
    t=np.linspace(0,12,200)
    t[100]=t[99]
    assert compare_two(t,np.sin(t),np.cos(t))['G3_phase_reproducibility']=='SCREEN_FAIL'

def test_stationary_euler_shear_and_galilean_invariance():
    from phaseclock import extract_shape_invariants
    n=8; x=2*np.pi*np.arange(n)/n
    u=np.zeros((4,n,n,n,3),dtype=float)
    u[...,1]=np.sin(x)[None,:,None,None]
    q1,q2,diag=extract_shape_invariants(u,2*np.pi)
    assert np.max(abs(q1-q1[0]))<1e-12
    assert np.max(abs(q2-q2[0]))<1e-12
    assert diag['divergence_rms_max_raw_units']<1e-12
    v=u.copy(); v[...,0]+=0.27;v[...,2]-=0.1
    p1,p2,_=extract_shape_invariants(v,2*np.pi)
    assert np.allclose(p1,q1,atol=1e-12)
    assert np.allclose(p2,q2,atol=1e-12)

def test_euler_time_rescale_observable():
    from phaseclock import measure_scalar_clock
    t=np.linspace(0,80,4001)
    q=np.sin(2*np.pi*0.25*t)
    a=measure_scalar_clock(t,q);b=measure_scalar_clock(t/2,q)
    assert a['status']==b['status']=='COHERENT_NUMERICAL_SCREEN'
    assert abs(b['omega']/a['omega']-2)<1e-10
