"""Independent new v0.4.3 numerical regressions; not physical certification."""
import numpy as np
import pytest
from experiment import material,rpo,floquet,dynamics
from experiment.euler3d import Euler3D,load_geometry,normalized_components
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[1]/'data/knot_3.1.txt'

def test_24_proper_cube_rotations():
    Rs=rpo.cube_rotations()
    assert len(Rs)==24
    assert len({tuple(M.ravel()) for M in Rs})==24
    assert all(round(np.linalg.det(M))==1 for M in Rs)

def test_exact_full_field_group_return_and_rotation_inversion():
    rng=np.random.default_rng(7)
    u=rng.normal(size=(3,12,12,12))
    R=rpo.cube_rotations()[7]; v=rpo.rotate_field(u,R)
    assert np.allclose(rpo.rotate_field(v,R.T),u)
    shifted=np.roll(v,(3,-2,4),axis=(1,2,3))
    found=rpo.best_translation(v,shifted,refine=True)
    assert found['residual']<1e-10
    inv=floquet.symmetry_inverse(shifted,R,[3,-2,4])
    assert np.linalg.norm(inv-u)/np.linalg.norm(u)<1e-10

def test_rpo_detector_uses_all_three_velocity_components():
    rng=np.random.default_rng(5)
    u=rng.normal(size=(3,12,12,12))
    fields=np.stack([u.transpose(1,2,3,0),np.roll(u,(2,1,-4),(1,2,3)).transpose(1,2,3,0)])
    # needs 3 frames by contract
    f=np.concatenate([fields,fields[-1:]])
    r=rpo.full_field_rpo(np.array([0.,1.,2.]),f,minimum_period=0.5,rotate=True)
    assert r['screen_pass'] and r['best']['residual']<1e-10
    assert r['certified_rpo'] is False

def test_material_rk4_is_identical_to_unchanged_A064_velocity_step():
    c,_=load_geometry(SOURCE);G=Euler3D(12,.4)
    U=G.velocity_from_curve(normalized_components(c)[0])
    S,_=material.create_torus(c)
    V,X=material.rk4_advect(G,U,S,.04)
    W,_=G.rk4(U,np.empty((0,*U.shape)),.04)
    assert np.array_equal(W,V) and np.linalg.norm(X-S)>0

def test_material_surface_does_not_auto_become_vortex_tube():
    j,arr,*_=dynamics.simulation(SOURCE,n=12,T=.8,dt=.04,snapshots=11)
    m=j['material_transport']
    assert m['material_advection_performed']
    assert not m['vortex_tube_qualified']
    assert arr['material_surface_unwrapped'].shape==(11,32,10,3)
    assert np.all(np.isfinite(arr['material_surface_unwrapped']))
    assert m['initial']['vorticity_tangency_mean_abs_cos']>.05

def test_global_closed_surface_flux_is_not_a_tangency_certificate():
    c,_=load_geometry(SOURCE);G=Euler3D(12,.4)
    U=G.velocity_from_curve(normalized_components(c)[0]);S,_=material.create_torus(c)
    d=material.diagnostics(G,U,S)
    assert d['vorticity_tangency_mean_abs_cos']>.05
    assert 'closed_surface_net_vorticity_flux' in d

def test_native_tangent_operator_finite_difference_consistency():
    c,_=load_geometry(SOURCE);G=Euler3D(12,.4)
    U=G.velocity_from_curve(normalized_components(c)[0]);q=G.project(np.random.default_rng(0).normal(size=U.shape))
    assert floquet.tangent_fd_test(G,U,q)<1e-6

def test_manufactured_floquet_oracle_no_target_fit():
    r=floquet.manufactured_floquet_test()
    assert r['oracle_pass']
    assert abs(r['expected_omega']-r['measured_omega'])<1e-12

def test_no_unqualified_physical_floquet_promotion():
    j,arr,*_=dynamics.simulation(SOURCE,n=12,T=.8,dt=.04,snapshots=11)
    assert j['physical_clock']=='UNRESOLVED'
    assert j['material_transport']['vortex_tube_qualified'] is False
