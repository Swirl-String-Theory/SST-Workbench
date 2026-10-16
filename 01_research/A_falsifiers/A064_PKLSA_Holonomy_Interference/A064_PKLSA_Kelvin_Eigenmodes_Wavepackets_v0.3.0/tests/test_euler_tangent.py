from pathlib import Path
import sys
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from euler_tangent import Euler3D,load_geometry,initial_condition,run_case,observe,normalized_components

P=ROOT/'data/knot_3.1.txt'

@pytest.fixture(scope='module')
def setup():
    geom,digest=load_geometry(P)
    g=Euler3D(12,.5)
    u,d,r,w,s=initial_condition(g,geom)
    return g,u,d,r,w,s

def test_source_records_are_actual_nonempty():
    g,sha=load_geometry(P)
    assert len(g)==1 and len(g[0])==47
    assert sha=='98a628af4ba5d09274f0a1845c351a7a3d633a39ff833a3ae0b78e351bafdabf'

def test_link_has_three_components():
    g,_=load_geometry(ROOT/'data/link_6.3.3.txt')
    assert [len(x) for x in g]==[35,30,32]

def test_nontrivial_vortex_background(setup):
    g,u,*_=setup
    assert np.sqrt(np.mean(np.sum(u*u,axis=0)))>1e-3

def test_zero_divergence_projection(setup):
    g,u,d,*_=setup
    assert g.divergence_relative(u)<1e-10
    assert all(g.divergence_relative(x)<1e-10 for x in d)

def test_zero_flow_has_zero_tangent_rhs(setup):
    g,u,d,*_=setup
    du,dd=g.rhs(np.zeros_like(u),d)
    assert np.max(np.abs(du))==0
    assert np.max(np.abs(dd))==0

def test_energy_preserved_short_evolution(setup):
    g,u,d,*_=setup
    E0=np.mean(np.sum(u*u,axis=0))
    for _ in range(6):u,d=g.rk4(u,d,.02)
    assert abs(np.mean(np.sum(u*u,axis=0))/E0-1)<1e-6

def test_superposition_of_tangent_perturbations(setup):
    g,u,d,*_=setup
    both=np.concatenate((d,d[:1]+d[1:2]),axis=0)
    _,result=g.rk4(u,both,.1)
    assert np.linalg.norm(result[2]-result[0]-result[1])/np.linalg.norm(result[2])<1e-12

def test_sign_reversal_cross_term(setup):
    g,u,d,r,w,s=setup
    a=observe(g,u,d,r,w)['delta_I']
    b=observe(g,u,np.stack((d[0],-d[1])),r,w)['delta_I']
    assert abs(a+b)<1e-12

def test_cross_term_equals_direct_inner_product(setup):
    g,u,d,r,w,s=setup
    a=observe(g,u,d,r,w)
    target=2*np.mean(w*np.sum(d[0]*d[1],axis=0))
    assert abs(target-a['delta_I'])<1e-12

def test_tangent_derivative_matches_centered_nonlinear(setup):
    g,u,d,*_=setup
    ep=1e-4
    Up,_=g.rk4(u+ep*d[0],np.empty((0,*u.shape)),.08)
    Um,_=g.rk4(u-ep*d[0],np.empty((0,*u.shape)),.08)
    _,D=g.rk4(u,d[:1],.08)
    fd=(Up-Um)/(2*ep)
    assert np.linalg.norm(fd-D[0])/np.linalg.norm(D[0])<1e-6

def test_receiver_basis_rotation_leaves_phase_advance_invariant():
    frame,meta=run_case(P,n=12,steps=10,dt=.04,core=.5)
    z=frame['z_A_re'].to_numpy()+1j*frame['z_A_im'].to_numpy()
    phi=np.unwrap(np.angle(z))
    phi2=np.unwrap(np.angle(z*np.exp(-.68j)))
    assert abs((phi[-1]-phi[0])-(phi2[-1]-phi2[0]))<1e-12

def test_geometry_coordinates_are_normalized_without_SI_claim():
    g,_=load_geometry(P)
    y,s=normalized_components(g)
    assert s>0
    assert np.all(y[0]>=0) and np.all(y[0]<2*np.pi)

def test_backend_has_no_hardcoded_pi_flux():
    # Static check is supplemental: no Z2/AB phase inserted by scientific kernel.
    txt=(ROOT/'src/euler_tangent.py').read_text()
    assert 'cos(2*np.pi*q' not in txt
    assert 'sin(2*np.pi*q' not in txt

def test_simulated_phase_is_nonstatic_and_finite():
    frame,meta=run_case(P,n=12,steps=20,dt=.04,core=.5)
    assert abs(meta['phase_A_change_rad'])>1e-4
    assert np.isfinite(meta['phase_B_change_rad'])
