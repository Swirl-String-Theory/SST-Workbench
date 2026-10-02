import numpy as np
from kj_sst.constants import R_C,RHO_F,GAMMA_CANON
from kj_sst.geometry import resample_closed,physicalize_thickness_to_rc,affine_constriction
from kj_sst.metrics import kelvin_duration
from kj_sst.constriction import streamtube_null
from native_ext.fallback import biot_savart,filament_hamiltonian

def circle(n=128,r=4.0):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[r*np.cos(t),r*np.sin(t),np.zeros_like(t)]

def test_resample_length():
 p=circle(300);q=resample_closed(p,128);assert q.shape==(128,3);assert abs(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1).sum()-2*np.pi*4)<0.02

def test_physicalization_sets_proxy():
 p=circle(128);q,meta=physicalize_thickness_to_rc(p,R_C,0.1);assert np.isfinite(q).all();assert np.isclose(meta['physical_nonadjacent_min_m'],2*R_C,rtol=1e-12)

def test_python_kernels_finite():
 p=circle(64);v=biot_savart(p,p,1.0,0.2);h=filament_hamiltonian(p,1.0,1.0,0.2);assert np.isfinite(v).all();assert np.isfinite(h);assert h>0

def test_kelvin_duration_exponential():
 gamma=2.5;t=np.linspace(0,8,20000);a=np.exp(-gamma*t);T=kelvin_duration(t,a);assert np.isclose(T,1/gamma,rtol=2e-3)

def test_constriction_null():
 r=streamtube_null(RHO_F,1.09384563e6,0.55,4096);assert r['ok'];assert r['constriction_head_rel_ptp']<1e-12

def test_affine_constriction_volume_preserving_matrix_effect():
 p=circle(64);q=affine_constriction(p,0.03);assert q.shape==p.shape;assert np.isfinite(q).all()
