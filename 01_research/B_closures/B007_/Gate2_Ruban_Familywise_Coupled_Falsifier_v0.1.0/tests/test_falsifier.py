import sys,io,json,hashlib
from pathlib import Path
import numpy as np
import pytest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
import falsifier as F
from reference_euler import EulerGrid,racetrack

@pytest.fixture(scope='session')
def inputs():return F.load_catalog()
def test_catalog_84_12_7(inputs):
 _,entries=inputs
 assert len(entries)==84
 from collections import Counter
 assert set(Counter(i['parametric_embedding'] for i,_,_ in entries).values())=={7}
def test_original_sha256_provenance(inputs):
 _,entries=inputs
 assert all(len(i['sha256'])==64 and len(i['perturbed_sha256'])==64 for i,_,_ in entries)
def test_closed_shape_preflight(inputs):
 _,entries=inputs
 g=F.geometry(entries[0][1]);assert g['length']>0 and g['min_segment']>0
def test_not_false_reach_certificate(inputs):
 _,entries=inputs
 assert 'not a geometric reach' in F.geometry(entries[0][1])['proxy_warning']
def test_geometry_B_ranges(inputs):
 _,entries=inputs
 P=next(p for i,p,_ in entries if i['seed_id']=='T_2_3_B1600_N512')
 assert abs(float(np.hypot(P[:,0],P[:,1]).min())-.84)<1e-10
 assert abs(float(np.hypot(P[:,0],P[:,1]).max())-1.16)<1e-10
def test_resampling_cycle_length(inputs):
 _,entries=inputs;P=entries[0][1];a=F.resample(P,256)
 assert len(a)==256 and abs(F.length(a)/F.length(P)-1)<.003
def test_induced_velocity_ring_is_axial():
 t=np.linspace(0,2*np.pi,80,endpoint=False);P=np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t)))
 v=F.induced_velocity(P,.08)
 assert np.max(abs(v[:,:2]))<1e-8 and np.min(v[:,2])>0
def test_rigid_fit_exact():
 t=np.arange(12)*np.pi/6;P=np.column_stack((np.cos(t),np.sin(t),np.zeros_like(t)))
 v=np.column_stack((-2*P[:,1],2*P[:,0],np.full(len(P),.3)))
 f=F.rigid_fit(P,v);assert f['relative_rigid_residual']<1e-12
 assert abs(f['Omega_z']-2.)<1e-12 and abs(f['U_z']-.3)<1e-12
def test_background_counts():
 assert [len(F.bg_grid_centres(k)) for k in ('single','triple','3x3','5x5')]==[1,3,9,25]
def test_background_curve_closure():
 P=F.bg_curve(racetrack(1.65,n_straight=30,n_arc=30),.3,.4)
 assert P.shape==(120,3)
 assert np.max(np.linalg.norm(np.diff(P,axis=0),axis=1))<.2
def test_fourier_closed_loop_zero_divergence():
 g=EulerGrid(12);k,diag=g.seed(racetrack(n_straight=20,n_arc=20),gamma=.05)
 assert diag['raw_fourier_divergence_ratio']<1e-8
 div=g.inv(1j*np.einsum('ixyz,ixyz->xyz',g.K,k))
 assert np.max(abs(div))<1e-9
def test_fixed_U_non_negative():
 g=EulerGrid(12);k,_=g.seed(racetrack(n_straight=20,n_arc=20),gamma=.05)
 a=F.evaluate_fixed(g,np.stack([k]),0.,12.)
 assert a['max_Rstar_fixedU']>=0 and a['max_Dstar']<1e-6
def test_euler_ABC_equilibrium():
 # Analytic stationary Arnold-Beltrami-Childress field: curl u = u.
 g=EulerGrid(12,2*np.pi);z=g.local;x,y,w=np.meshgrid(z,z,z,indexing='ij')
 u=np.stack((np.sin(w)+np.cos(y),np.sin(x)+np.cos(w),np.sin(y)+np.cos(x)))
 oh=g.fwd(u);rr=g.inv(g.rhs(np.stack([oh]))[0]);assert np.sqrt(np.mean(rr*rr))<1e-10


def test_g4_proximity_preflight_warns_intersections():
 P=F.bg_curve(racetrack(n_straight=18,n_arc=18),0,0)
 q=F.bg_curve(racetrack(n_straight=18,n_arc=18),0,0)
 a=F.sampled_component_separation([P,q])
 assert a['minimum_sampled_vertex_distance']<1e-12

def test_g4_proximity_preflight_allows_separated_curves():
 P=F.bg_curve(racetrack(n_straight=18,n_arc=18),0,0)
 q=P+np.array([0.,3.,0.])
 a=F.sampled_component_separation([P,q]);assert abs(a['minimum_sampled_vertex_distance']-3)<1e-12
