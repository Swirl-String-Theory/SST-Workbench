import numpy as np
from master_mass.geometry import resample_closed,normalize_by_reach,rigid_transform,descriptors,linking_number
from master_mass.energy import energy_matrix,relative_l2,decomposition
from master_mass.dynamics import gradient_hessian,mass_matrix,jacobian,spectrum

def circle(n=96,z=0.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[np.cos(t),np.sin(t),np.full(n,z)]

def test_resample_closed_length():
    c=circle(32);r=resample_closed(c,128);assert r.shape==(128,3);assert abs(descriptors([r])['length']-2*np.pi)<0.02

def test_reach_normalization_positive():
    c=circle();norm,reach,_=normalize_by_reach([c]);assert reach>0;assert descriptors(norm)['reach']>0

def test_energy_rigid_invariance():
    c=[circle(72)];a=energy_matrix(c,1.0);b=energy_matrix(rigid_transform(c),1.0);assert relative_l2(a,b)<1e-12

def test_energy_decomposition():
    a=circle(64);b=circle(64,z=2.2);E=energy_matrix([a,b],0.5);d=decomposition(E);assert d['closure_error']<1e-15;assert np.allclose(E,E.T)

def test_hessian_quadratic():
    A=np.array([[2.0,.3],[.3,5.0]])
    U=lambda q: .5*np.asarray(q)@A@np.asarray(q)
    _,g,K=gradient_hessian(U,2,1e-4);assert np.linalg.norm(g)<1e-9;assert np.allclose(K,A,rtol=2e-6,atol=2e-6)

def test_jacobian_spectrum():
    M=mass_matrix(2);K=np.diag([4.0,9.0]);J,lam,f=spectrum(M,K);assert J.shape==(4,4);assert np.allclose(sorted(f),[2.0,3.0],rtol=1e-8)

def test_circle_reach_normalized_ropelength():
    c=circle(128);norm,reach,_=normalize_by_reach([c]);rl=descriptors(norm)['ropelength_proxy'];assert 0.9<reach<1.05;assert abs(rl-2*np.pi)<0.2

def test_tube_energy_finite_positive():
    from master_mass.volume_energy import tube_energy_kernel
    c=circle(48);norm,_,_=normalize_by_reach([c]);e,meta=tube_energy_kernel(norm,1.0,1,4);assert e>0 and np.isfinite(e);assert meta['sample_count']==48*4
