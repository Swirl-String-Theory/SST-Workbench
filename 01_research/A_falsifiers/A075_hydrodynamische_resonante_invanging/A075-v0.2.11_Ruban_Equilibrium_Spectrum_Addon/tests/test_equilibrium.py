from pathlib import Path
import math
import numpy as np
import pytest
from ruban_equilibrium.runner import verify,PRIMARY,ROOT,SOURCE_HASH,SEED_HASH
from ruban_equilibrium.core import (torus,derivative,field,fitted_residual,relax,
                                    numerical_spectral_proxy,B_REFERENCE,GAMMA,DELTA,LAMBDA,LOCAL_COEFFICIENT)

def test_a007_and_a075_hashes():
    x=verify()
    assert x['A007_primary_sha256']==SEED_HASH
    assert x['A075_parent_solver_sha256']==SOURCE_HASH
    assert x['A007_max_torus_residual']<1e-12

def test_paper_parameter_algebra():
    assert B_REFERENCE == 77/500
    assert DELTA == 1/20
    assert abs(LAMBDA-(1.4+math.log(200)/2))<1e-13
    assert abs(LOCAL_COEFFICIENT-0.5267132048600136)<1e-14

def test_known_torus_length():
    x=torus(B_REFERENCE,128)
    v=derivative(x,1)
    assert abs(np.linalg.norm(v,axis=1).sum()*2*math.pi/128 - 12.90102710256)<1e-8
    rad=np.hypot(x[:,0],x[:,1]); assert np.max(np.abs(np.hypot(rad-1,x[:,2])-B_REFERENCE))<1e-13

def test_ring_field_is_axial_symmetry():
    n=128; th=np.arange(n)*2*np.pi/n
    x=np.column_stack((np.cos(th),np.sin(th),np.zeros(n)))
    v=field(x)
    assert np.max(np.std(v,axis=0))<2e-10
    fit=fitted_residual(x,v)
    assert fit['epsilon']<1e-10

def test_analytic_trefoil_regression():
    x=torus(B_REFERENCE,128)
    fit=fitted_residual(x)
    assert abs(fit['epsilon']-0.0570915190824)<5e-9
    assert fit['rms_velocity']>0
    assert np.isfinite(fit['U']) and np.isfinite(fit['Omega'])

def test_relax_reduces_approximate_residual():
    v=relax(B_REFERENCE,96,harmonics=1,max_nfev=20)
    assert v['final_epsilon']<v['initial_epsilon']
    assert len(v['coeff'])==4

def test_proxy_is_uncertified_and_finite():
    x=torus(B_REFERENCE,64)
    fit=fitted_residual(x)
    p=numerical_spectral_proxy(x,fit['U'],fit['Omega'],modes=2)
    assert p['mode_count']==8
    assert np.isfinite(p['max_real_part'])
    assert 'UNCERTIFIED' in p['status']

def test_bad_geometry_refused():
    with pytest.raises(ValueError):torus(0,128)
    with pytest.raises(ValueError):torus(.154,33)
    with pytest.raises(ValueError):torus(.154,128,p=2,q=4)

def test_a007_actual_vertices_used_by_uniform_theta_adapter():
    from ruban_equilibrium.runner import load_a007_at_uniform_theta
    p=load_a007_at_uniform_theta(128)
    assert p.shape==(128,3)
    assert np.max(np.abs(p-torus(B_REFERENCE,128)))<3e-11
    fit=fitted_residual(p)
    assert np.isfinite(fit['epsilon'])
    v=relax(B_REFERENCE,64,harmonics=1,max_nfev=12,reference_points=load_a007_at_uniform_theta(64))
    assert v['final_epsilon']<v['initial_epsilon']
