"""Independent invariant, orientation, and manufactured-residual regressions."""
from __future__ import annotations
import math
import numpy as np
import pytest
from ruban_equilibrium.core import torus, GAMMA, DELTA, derivative
from ruban_equilibrium.free_gauge_nk import (GaugeSlice, axial_spin, eval_system, jvp,
                                             solve, prolongate, InvalidCurve)
from ruban_equilibrium.high_order import field as reference_field
from ruban_equilibrium.fast_field import field as fast_field, _sum
from ruban_equilibrium.runner import verify,load_a007_at_uniform_theta


def test_source_immutability():assert verify()['status'].startswith('PROVENANCE_VERIFIED')

def test_normal_frame_gauge_independence():
    g=GaugeSlice.from_reference(torus(.154,64))
    assert np.allclose(g.phase_orthobasis.T@g.phase_orthobasis,np.eye(2),atol=1e-12)
    assert np.max(np.abs(np.sum(g.normal1*g.normal2,axis=1)))<1e-12
    assert np.max(np.abs(np.linalg.norm(g.normal1,axis=1)-1))<1e-12

def test_manufactured_exact_axial_motion():
    x=torus(.154,64);g=GaugeSlice.from_reference(x);U=1.7;Omega=.35
    def artificial(a):return U*np.array([0.,0.,1.])+Omega*axial_spin(a)+.25*derivative(a)
    y=g.y0(U,Omega)
    f,m=eval_system(g,y,velocity_function=artificial)
    assert np.linalg.norm(f)<1e-12
    assert m['epsilon']<1e-12
    ans=solve(x,initial=y,velocity_function=artificial,max_newton=2)
    assert ans['status']=='FINITE_N_CANDIDATE'

def test_jvp_captures_unknown_screw_speeds():
    g=GaugeSlice.from_reference(torus(.154,64));y=g.y0()
    v=np.zeros_like(y);v[-2]=1
    jj=jvp(g,y,v,fd_step=1e-6)
    # u = U / Gamma, the derivative is -P e_z in the shape equations.
    assert abs(np.linalg.norm(jj[:-2])/np.sqrt(g.n)-1.0)<.2
    assert np.linalg.norm(jj[-2:])<1e-10

def test_prolongation_keeps_phases_fixed():
    g=GaugeSlice.from_reference(torus(.154,64))
    y=g.y0(2.2,1.5)
    gg,z=prolongate(g,y,torus(.154,128))
    assert z.shape==(258,)
    assert np.linalg.norm(gg.phase(z))<1e-12
    assert np.max(np.abs(z[-2:]-y[-2:]))<1e-12

def test_independent_quadratures_on_actual_geometry():
    a=load_a007_at_uniform_theta(64)
    assert np.linalg.norm(reference_field(a))>0
    if _sum is not None:
        for scheme in ('trapezoid','midpoint'):
            assert np.max(np.abs(reference_field(a,scheme=scheme)-fast_field(a,scheme=scheme)))<3e-12

def test_fail_closed_for_bad_chart_and_singular_curve():
    g=GaugeSlice.from_reference(torus(.154,64))
    y=g.y0();y[0]=1.5
    with pytest.raises(InvalidCurve):eval_system(g,y)
    with pytest.raises(InvalidCurve):g.coordinates(np.ones(5))

def test_real_ruban_relaxation_beats_restricted_fourier():
    x=load_a007_at_uniform_theta(64)
    r=solve(x,max_newton=6,gmres_cycles=2,gmres_restart=35)
    assert np.isfinite(r['summary']['epsilon'])
    assert r['summary']['epsilon']<.005  # cannot certify continuum from this
    assert r['exact_equilibrium_proven'] is False
    assert r['physical_stability']=='UNRESOLVED'
