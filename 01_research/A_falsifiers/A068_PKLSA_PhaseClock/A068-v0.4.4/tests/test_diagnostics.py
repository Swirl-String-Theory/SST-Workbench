from __future__ import annotations
import numpy as np
from diagnostics.variational import (spectral_value_jacobian,trilinear_value_jacobian,
            compare_interpolators,compare_deformation_methods)
from diagnostics.mesh_intersections import all_nonincident_intersections,intersects_sat
from diagnostics.fieldline_tube import trace_poincare_ring
from diagnostics.xpu_probe import probe

class ToyGrid:
    def __init__(self,n=8):
        self.n=n;self.dx=2*np.pi/n
        k=np.fft.fftfreq(n,d=1./n)
        self.k=np.asarray(np.meshgrid(k,k,k,indexing='ij'))
        self.mask=np.all(np.abs(self.k)<=n//3,axis=0)
        self.mask[0,0,0]=False
        x=(np.arange(n)+.5)*self.dx
        self.coords=np.asarray(np.meshgrid(x,x,x,indexing='ij'))
    def project(self,U):
        f=np.fft.fftn(U,axes=(-3,-2,-1))*self.mask
        k2=np.sum(self.k*self.k,axis=0)
        inv=np.zeros_like(k2);inv[k2>0]=1/k2[k2>0]
        f-=self.k*(np.sum(self.k*f,axis=0)*inv)
        return np.fft.ifftn(f*self.mask,axes=(-3,-2,-1)).real
    def rhs(self,U,D):return np.zeros_like(U),D

def test_spectral_interpolant_is_exact_on_cell_centers():
    g=ToyGrid();U=g.project(np.random.default_rng(14).normal(size=(3,8,8,8)))
    x=np.moveaxis(g.coords,0,-1)
    sampled,J=spectral_value_jacobian(g,U,x)
    assert np.linalg.norm(sampled-np.moveaxis(U,0,-1))<1e-12
    assert np.max(np.abs(np.trace(J,axis1=-2,axis2=-1)))<1e-12

def test_trilinear_can_cause_false_volume_growth():
    g=ToyGrid();U=g.project(np.random.default_rng(42).normal(size=(3,8,8,8)))
    X=np.random.default_rng(52).uniform(.3,5.8,size=(5,3))
    audit=compare_interpolators(g,U,X)
    assert audit['max_spectral_divergence']<1e-12
    assert audit['max_trilinear_divergence']>1e-3
    s=compare_deformation_methods(g,U,X,.01,3,method='spectral')
    t=compare_deformation_methods(g,U,X,.01,3,method='trilinear')
    assert s['history'][-1]['detF_var_error_max']<1e-8
    assert t['history'][-1]['detF_var_error_max']>1e-5
    assert t['history'][-1]['F_sat_vs_var_rel']<2e-3  # trilinear J jumps at cell boundaries; satellites can cross cells

def test_triangle_intersections_and_clean_case():
    A=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]])
    B=np.array([[.3,.3,-1.],[.3,.3,1.],[.4,.4,0.]])
    C=np.array([[3.,0.,0.],[4.,0.,0.],[3.,1.,0.]])
    assert intersects_sat(A,B)
    assert not intersects_sat(A,C)
    crossed=all_nonincident_intersections(np.concatenate([A,B]),np.array([[0,1,2],[3,4,5]]))
    clean=all_nonincident_intersections(np.concatenate([A,C]),np.array([[0,1,2],[3,4,5]]))
    assert crossed['nonincident_intersection_count']==1
    assert clean['nonincident_intersection_count']==0
    assert not clean['full_surface_certified']

def test_poincare_oracle_and_nonclosure():
    c=np.array([3.,3.,3.]);x=c+np.array([1.,0.,0.])
    def field(p):
        v=p-c;return np.stack([-v[:,1],v[:,0],np.zeros(len(v))],axis=-1)
    ok=trace_poincare_ring(field,x,radius=.1,sides=8,smax=10,max_step=.2)
    assert ok['section_invariance_screen_pass']
    assert ok['max_return_set_mismatch']<1e-7
    assert not ok['flux_surface_candidate_qualified']

def test_hardware_probe_never_fake_claims():
    r=probe()
    assert r['physical_fp64_claim']=='FORBIDDEN_ON_ARC_A770'
    if r['status']=='NO_XPU':assert not r['hardware_gpu_executed']
