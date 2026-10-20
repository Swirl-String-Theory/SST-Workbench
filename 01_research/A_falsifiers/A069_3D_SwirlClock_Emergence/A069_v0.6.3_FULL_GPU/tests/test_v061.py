import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from a069_v061.geometry_gate import segment_distance,geometry_screen,readiness
from a069_v061.subgrid import bilinear_zero,subgrid_filaments,compare_filaments

def ring_field(n=24):
    x,y,z=np.meshgrid(2*np.pi*np.arange(n)/n,2*np.pi*np.arange(n)/n,2*np.pi*np.arange(n)/n,indexing='ij')
    return (np.cos(x)+np.cos(y)-1.36+1j*np.sin(z+.18)).astype(complex)
def test_segment_crossing_distance():
    d=segment_distance(np.array([0.,0,0]),np.array([1.,0,0]),np.array([.5,-1.,0]),np.array([.5,1.,0]))
    assert d<1e-12
def test_segment_skew_distance():
    d=segment_distance(np.array([0.,0,0]),np.array([1.,0,0]),np.array([.5,.5,1]),np.array([.5,.5,-1]))
    assert np.isclose(d,.5)
def test_bilinear_subgrid_analytic_root():
    u,v=.23,.71
    # bilinear complex affine face with unique interior zero
    f=lambda x,y: (x-u)+1j*(y-v)
    z=np.array([f(0,0),f(1,0),f(1,1),f(0,1)])
    out,err=bilinear_zero(z)
    assert err<1e-12 and np.linalg.norm(out-np.array([u,v]))<1e-11
def test_bilinear_reject_nonintersecting():
    z=np.array([1+1j,2+1j,2+2j,1+2j]);out,err=bilinear_zero(z)
    assert out is None and err>1e-4
def test_core_gate_fails_coarse_grid():
    s={'approx_min_nonlocal_segment_distance':1.,'max_discrete_curvature':.2}
    o=readiness(s,xi=.42,n=32,box=10)
    assert not o['qualified'] and not o['gates']['core_resolution']
def test_core_gate_fails_close_filaments():
    s={'approx_min_nonlocal_segment_distance':.284,'max_discrete_curvature':.2}
    assert not readiness(s,xi=.42,n=256,box=10)['qualified']
def test_core_gate_full_pass_only_if_all_three():
    s={'approx_min_nonlocal_segment_distance':2.,'max_discrete_curvature':.1}
    assert readiness(s,xi=.2,n=256,box=10)['qualified']
def test_simple_circle_geometry_screen():
    t=np.linspace(0,2*np.pi,256,endpoint=False)
    x=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    s=geometry_screen(x,neighbor_k=64)
    assert s['length']>6 and s['max_discrete_curvature']>0.95
    assert s['approx_min_nonlocal_segment_distance']>0
def test_subgrid_two_rings():
    o=subgrid_filaments(ring_field(),box=2*np.pi)
    assert o['components_count']==2 and o['unlocalized_faces']==0
    assert o['subgrid_reconstruction_qualified']
    assert all(c['subgrid_polyline'] is not None for c in o['components'])
    assert all(c['periodic_homology']==[0,0,0] for c in o['components'])
def test_subgrid_gauge_phase():
    p=ring_field();x=subgrid_filaments(p)
    y=subgrid_filaments(p*np.exp(1j*.357))
    assert x['components_count']==y['components_count']
    assert sorted(round(c['subgrid_length'],9) for c in x['components'])==sorted(round(c['subgrid_length'],9) for c in y['components'])
def test_subgrid_shift_one_cell():
    p=ring_field();x=subgrid_filaments(p)
    y=subgrid_filaments(np.roll(p,1,axis=1))
    assert len(x['components'])==len(y['components'])
    assert np.allclose(sorted(c['subgrid_length'] for c in x['components']),sorted(c['subgrid_length'] for c in y['components']))
def test_comparison_does_not_certify_reconnection_or_clock():
    q=subgrid_filaments(ring_field())
    c=compare_filaments(q,q)
    assert c['topology_status']=='UNRESOLVED' and not c['reconnection_certified']
    assert not q['knot_type_certified']

def test_analytic_zero_on_boundary_fail_closed():
    u,v=.55,1.
    f=lambda x,y: (x-u)+1j*(y-v)
    zz=np.array([f(0,0),f(1,0),f(1,1),f(0,1)])
    out,err=bilinear_zero(zz)
    assert out is None and err==0

def test_fourier_shift_keeps_periodic_plane_wave():
    from a069_v061.subgrid import spectral_grid_shift
    n=24; box=2*np.pi
    x=np.arange(n)*box/n
    psi=np.exp(2j*x)[:,None,None]*np.ones((1,n,n))
    d=.37*box/n
    shifted=spectral_grid_shift(psi,box,(.37,0,0))
    assert np.max(abs(shifted-psi*np.exp(2j*d)))<1e-11
