import numpy as np
from a060_preflight.mechanics import (diagnostics,balanced,rank_one,rank_two,rank_one_gate,
    landreman_field,landreman_kinematic_pressure,finite_jacobian,direct_spherical_flux,gradient_flux_prediction)
from a060_preflight.projection import projection_demo


def test_silent_and_balanced():
    a=diagnostics(rank_one()); b=diagnostics(balanced()); c=diagnostics(rank_two())
    for d in (a,b,c): assert abs(d['poisson_source'])<1e-12 and abs(d['chi'])<1e-12
    assert abs(a['f']-1)<1e-12 and abs(b['f'])<1e-12
    assert abs(b['Vs']-3)<1e-12 and abs(b['fluxfactor'])<1e-12
    assert abs(c['r1']-.5)<1e-12


def test_gate_scaling():
    for s in [-1,1]:
        A=rank_one_gate(eps=.01,sign=s); d=diagnostics(A)
        assert abs(d['poisson_source']+2*s*.01)<1e-12
        lam=np.linalg.eigvals(A)
        assert abs(max(abs(lam))-.1)<1e-12
    d=diagnostics(rank_two(eps=.01))
    assert abs(d['poisson_source'])<1e-12
    assert abs(max(abs(np.linalg.eigvals(rank_two(eps=.01))))-.01**(1/3))<1e-12


def test_shear_wedge():
    rng=np.random.default_rng(20261013)
    for _ in range(2500):
        A=rng.normal(size=(3,3))
        A-=np.trace(A)/3*np.eye(3)
        d=diagnostics(A)
        assert d['m']-1e-10 <= 1-d['f'] <= 3*d['m']+1e-10
        assert abs(d['chi']-2*abs(d['Q'])/np.sum(A*A))<1e-12


def test_landreman():
    for eps in (0,.2,.5):
        x=np.array([1.04,.16,.04])
        fun=lambda y:landreman_field(y,eps)
        u=fun(x); A=finite_jacobian(fun,x,h=1e-5)
        assert abs(np.trace(A))<3e-7
        assert np.max(np.abs(A@u+x*np.array([1,1,4])))<2e-7
        assert abs(diagnostics(A)['poisson_source']-6)<3e-6
        assert abs(landreman_kinematic_pressure(x)-.5*(x[0]**2+x[1]**2+4*x[2]**2))<1e-15


def test_flux_against_spherical_integral():
    rng=np.random.default_rng(7189)
    for A in (rank_one(),balanced(),rank_two(eps=.02), *[rng.normal(size=(3,3)) for _ in range(15)]):
        A=A-np.trace(A)/3*np.eye(3)
        pred=gradient_flux_prediction(A,diameter=.7)
        integ=direct_spherical_flux(A,diameter=.7)
        assert abs(pred-integ)<1e-12*(1+abs(pred))


def test_solenoidal_va_projection():
    d=projection_demo(25)
    assert d['non_solenoidal_va_max']>.01
    assert d['local_omega_gradphi_max']>1e-5
    assert abs(d['mean_omega_gradphi'])<1e-9
    assert d['projection_curl_error']<1e-8
    assert d['divergence_projected_va']<1e-8
