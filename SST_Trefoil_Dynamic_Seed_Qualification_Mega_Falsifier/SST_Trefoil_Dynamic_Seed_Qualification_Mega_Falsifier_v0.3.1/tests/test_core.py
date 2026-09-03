import numpy as np
from sst_seed_falsifier.candidates import analytic_trefoil
from sst_seed_falsifier.geometry import resample_closed,normalize_length,align_cyclic,min_nonlocal_vertex_distance,fourier_normal_basis
from sst_seed_falsifier.solver import velocity_py

def test_geometry_and_alignment():
    x=normalize_length(resample_closed(analytic_trefoil(256),64),2*np.pi); a,d,*_=align_cyclic(x,x,4); assert d<1e-12; assert min_nonlocal_vertex_distance(x,3)>0

def test_basis():
    x=normalize_length(resample_closed(analytic_trefoil(256),64),2*np.pi); B,L=fourier_normal_basis(x,2); assert len(B)>=6; G=B.reshape(len(B),-1)@B.reshape(len(B),-1).T; assert np.max(np.abs(G-np.eye(len(B))))<1e-8

def test_velocity_finite():
    x=normalize_length(resample_closed(analytic_trefoil(256),32),2*np.pi); u=velocity_py(x,1.0,np.full(len(x),.08)); assert np.isfinite(u).all()
