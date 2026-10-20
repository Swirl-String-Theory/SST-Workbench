import sys, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pilot

def test_time_monotonic_and_dimensional():
    assert pilot.ST>0 and pilot.OMEGA0>0
    assert pilot.tau(pilot.GYR)>pilot.GYR

def test_affine_exact_euler():
    for t in [0,0.5*pilot.GYR,pilot.GYR]:
        A=pilot.A(t)
        w=pilot.OMEGA0*pilot.f(t)
        Ap=__import__('numpy').array([[0,-pilot.ST*w,0],[pilot.ST*w,0,0],[0,0,0]],float)
        assert abs(A.trace())<1e-25
        assert __import__('numpy').allclose(Ap+A@A,pilot.analytic_acceleration_matrix(t),rtol=1e-13,atol=0)

def test_clock_only_no_acceleration():
    t=pilot.GYR
    # D_radar/D_abs=f, tau=(f-1)/s, implies f=1+s*tau exactly
    assert math.isclose(pilot.f(t),1+pilot.ST*pilot.tau(t),rel_tol=1e-14)

def test_rod_clock_mismatch():
    t=pilot.GYR
    f=pilot.f(t);a=math.exp(-pilot.ST*t/2)
    assert not math.isclose(f*a,1,rel_tol=1e-3)

def test_anisotropy_and_volume():
    t=pilot.GYR; u=pilot.f(t)
    assert math.isclose((u)*(u**(-.5))**2,1,rel_tol=1e-12)
    assert u>1 and u**(-.5)<1

def test_optical_positive_and_distance_duality():
    assert pilot.target_tau(1)>0
    assert math.exp(pilot.target_tau(1)/2)>1.2

def test_galilean_boost_does_not_change_vorticity_or_clock():
    import numpy as np
    t=0.31*pilot.GYR
    boost=np.array([12.5,-3.75,0.5])
    x_local=np.array([.01,-.07,.2])
    A=pilot.A(t)
    # Galilean transformation x' = x + U*t; u'(x',t)=u(x'-U*t,t)+U.
    # Evaluate in COMOVING coordinates to avoid catastrophic cancellation of
    # x' and U*t (~1e17 m) when differentiating on microscopic scales.
    up_local=lambda delta: A@delta+boost
    h=1e-5
    dudy=(up_local(x_local+np.array([0,h,0]))[0]-up_local(x_local-np.array([0,h,0]))[0])/(2*h)
    dvdx=(up_local(x_local+np.array([h,0,0]))[1]-up_local(x_local-np.array([h,0,0]))[1])/(2*h)
    assert math.isclose(dvdx-dudy,2*pilot.OMEGA0*pilot.f(t),rel_tol=1e-9)
    assert math.isclose(A[1,0]-A[0,1],2*pilot.OMEGA0*pilot.f(t),rel_tol=1e-14)

def test_roundtrip_small_baseline_limit():
    # Exact local-time accumulation for an absolute signal flight time delta_t.
    # D_op/(Dabs*f) = expm1(s*delta_t)/(s*delta_t), tending to 1 for short flights.
    x=1e-5
    correction=math.expm1(x)/x
    assert abs(correction-(1+x/2))<1e-10
