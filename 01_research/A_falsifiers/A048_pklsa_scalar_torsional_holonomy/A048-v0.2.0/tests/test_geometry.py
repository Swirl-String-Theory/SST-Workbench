import numpy as np
from sst_torsion.geometry import circle,curvature_torsion,bishop_frame,winding_number,trefoil

def test_circle_geometry():
    k,t,_,_=curvature_torsion(circle(512,1.0))
    assert abs(np.mean(k)-1.0)<1e-6
    assert np.max(np.abs(t))<1e-8

def test_bishop_frame_orthonormal():
    T,N,B,h=bishop_frame(trefoil(512))
    assert np.max(np.abs(np.sum(T*N,axis=1)))<1e-10
    assert np.max(np.abs(np.linalg.norm(T,axis=1)-1))<1e-10
    assert np.isfinite(h)

def test_winding_gauge_invariance():
    th=np.linspace(0,2*np.pi,1024,endpoint=False); chi=3*th
    assert abs(winding_number(chi)-3)<1e-10
    assert abs(winding_number(chi+0.731)-3)<1e-10
