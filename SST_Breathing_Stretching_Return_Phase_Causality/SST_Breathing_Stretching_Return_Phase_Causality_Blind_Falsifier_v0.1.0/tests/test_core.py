import numpy as np
from sst_bsrp_falsifier.geometry import synthetic_ring,resample_closed,normalize,perturb,radius_gyration
from sst_bsrp_falsifier.solver import velocity_python,velocity_variable_core_python,segment_lengths,segment_cores,stretch_rate_python
from sst_bsrp_falsifier.observables import analytic_signal,breathing_harmonic_phase,packet_track

def test_breathing_perturbation():
    x,_=normalize(resample_closed(synthetic_ring(100),64)); y=perturb(x,.01,1,0,1,0,.05)
    assert abs(radius_gyration(y)/radius_gyration(x)-1-.01)<2e-4

def test_ring_velocity_finite():
    x,_=normalize(resample_closed(synthetic_ring(100),48)); u=velocity_python(x,1,.05); s=stretch_rate_python(x,u)
    assert np.isfinite(u).all() and np.isfinite(s).all()

def test_material_core_volume_invariant():
    x,_=normalize(resample_closed(synthetic_ring(100),48)); ref=segment_lengths(x); y=x.copy(); y[1]=y[0]+1.2*(y[1]-y[0])
    a=segment_cores(y,ref,.05,-.5); ell=segment_lengths(y)
    assert np.max(np.abs(a*a*ell/(.05*.05*ref)-1))<1e-12

def test_variable_core_zero_exponent_equals_fixed_core():
    x,_=normalize(resample_closed(synthetic_ring(100),48)); u=velocity_python(x,1,.05); uv=velocity_variable_core_python(x,1,np.full(len(x),.05))
    assert np.linalg.norm(u-uv)/np.linalg.norm(u)<1e-12

def test_analytic_signal_shape():
    t=np.linspace(0,4*np.pi,256,endpoint=False); z=analytic_signal(np.cos(t)); assert np.median(np.abs(np.abs(z)-1))<1e-6

def test_harmonic_return_phase():
    t=np.linspace(0,10,201); w=2.3; d=.4; q=.02*np.cos(w*t-d); tau=3.2
    r=breathing_harmonic_phase(t,q,tau,161); expected=np.angle(np.exp(1j*(w*tau-d)))
    err=abs(np.angle(np.exp(1j*(r['phase_rad']-expected))))
    assert r['available'] and r['harmonic_r2']>.999 and err<.03

def test_synthetic_packet_full_return():
    N=64; M=100; t=np.linspace(0,1,M); j=np.arange(N); ref=np.exp(-.5*(np.angle(np.exp(1j*(2*np.pi*j/N)))/.35)**2)
    S=np.asarray([np.roll(ref,int(round(z*N))) for z in np.linspace(0,1.25,M)])
    r=packet_track(S,t,.1); assert r['available'] and abs(r['tau_return']-.81)<.05
