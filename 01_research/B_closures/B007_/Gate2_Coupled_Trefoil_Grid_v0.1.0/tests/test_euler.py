import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from euler_coupled import (EulerGrid,source_points,racetrack,length,exact_polygon_fourier,make_config)


def test_source_is_closed_polygon_with_positive_length():
    for name in ('T_2_3_B1600_N512','T_3_2_B1600_N512'):
        pts,path=source_points(name)
        assert len(pts)==512
        assert path.is_file()
        assert 12 < length(pts) <20
        assert np.max(np.abs(pts))<1.2


def test_return_stadium_is_closed_and_no_endpoints():
    pts=racetrack(n_straight=24,n_arc=24)
    assert abs(pts[0,0])<1e-12
    assert min(pts[:,2])<-1.3
    assert max(pts[:,2])>1.3
    assert np.linalg.norm(np.sum(np.roll(pts,-1,axis=0)-pts,axis=0)) <1e-12


def test_exact_polygon_fourier_solenoidality():
    g=EulerGrid(16)
    pts,_=source_points('T_2_3_B1600_N512')
    w,diag=g.seed(pts)
    assert diag['raw_fourier_divergence_ratio']<1e-12
    assert diag['zero_mode']<1e-10
    assert np.max(np.abs(np.einsum('ixyz,ixyz->xyz',g.K,w)))<1e-9


def test_curl_gradient_zero_and_div_curl_zero():
    g=EulerGrid(16)
    rng=np.random.default_rng(41)
    f=g.fwd(rng.standard_normal((16,16,16)))*g.filter
    grad=1j*g.K*f
    gradcurl=g.curl(grad)
    assert np.max(np.abs(gradcurl))<1e-10
    a=g.fwd(rng.standard_normal((3,16,16,16)))*g.filter
    curl=g.curl(a)
    assert np.max(np.abs(np.einsum('ixyz,ixyz->xyz',g.K,curl)))<1e-10


def test_background_alone_is_different_from_coupled():
    g=EulerGrid(16)
    pts,_=source_points('T_2_3_B1600_N512')
    k,_=g.seed(pts)
    b,_=g.seed(racetrack(n_straight=24,n_arc=24),gamma=.10)
    bg_alone=g.rhs(np.stack([b]))[0]
    bg_coupled=g.rhs(np.stack([k,b]))[1]
    assert np.linalg.norm(bg_coupled-bg_alone)>1e-4


def test_full_rk4_leaves_solenoidal_species():
    g=EulerGrid(16)
    pts,_=source_points('T_2_3_B1600_N512')
    k,_=g.seed(pts)
    b,_=g.seed(racetrack(n_straight=24,n_arc=24),gamma=.05)
    before=np.stack([k,b]);after=g.rk4(before,1e-4)
    assert np.max(np.abs(np.einsum('ixyz,aixyz->axyz',g.K,after)))<1e-8
    assert np.linalg.norm(after[0]-before[0])>1e-10
    assert np.linalg.norm(after[1]-before[1])>1e-10


def test_frozen_control_is_explicitly_non_euler():
    g=EulerGrid(16)
    pts,_=source_points('T_2_3_B1600_N512')
    k,_=g.seed(pts)
    b,_=g.seed(racetrack(n_straight=24,n_arc=24),gamma=.10)
    a=np.stack([k,b]);frozen=g.rk4(a,1e-4,True)
    assert np.array_equal(frozen[1],a[1]*g.filter)
    assert np.linalg.norm(frozen[0]-a[0])>1e-11


def test_no_sst_hardcoding():
    c=make_config()
    assert c['gamma_bg']==0.05
    assert c['sigma']==.12
    assert c['n']==32


def test_abc_beltrami_is_stationary_in_both_euler_forms():
    g=EulerGrid(16)
    v=2*np.pi/g.box
    x=g.local[:,None,None]; y=g.local[None,:,None]; z=g.local[None,None,:]
    X,Y,Z=np.broadcast_arrays(x,y,z)
    A,B,C=1.0,.6,.3
    u=np.stack((A*np.sin(v*Z)+C*np.cos(v*Y),
                 B*np.sin(v*X)+A*np.cos(v*Z),
                 C*np.sin(v*Y)+B*np.cos(v*X)))
    w=v*u
    stat=g.diagnostics(np.stack([g.fwd(w)]), L0=10.)
    assert stat['component_residuals'][0]['euler_residual_rms']<1e-12
    assert stat['momentum_projected_R_star']<1e-8
    assert stat['max_D_star']<1e-8


def test_translating_ring_detects_physical_speed_in_one_basis():
    g=EulerGrid(32)
    p=np.arange(160)*2*np.pi/160
    circ=np.stack((np.cos(p),np.sin(p),np.zeros_like(p)),axis=1)
    w,_=g.seed(circ)
    out=g.diagnostics(w[None],2*np.pi)
    # This test catches mistakenly fitting physical derivatives to Fourier RHS.
    assert 0.1 < out['U_z_fitted'] < 0.5
    assert out['component_residuals'][0]['relative_to_induced_rms'] < 0.95


def test_cross_induction_exactly_matches_coupled_minus_background_only_rhs():
    g=EulerGrid(16)
    pts,_=source_points('T_2_3_B1600_N512')
    k,_=g.seed(pts)
    b,_=g.seed(racetrack(n_straight=24,n_arc=24),gamma=.05)
    coupled=g.rhs(np.stack([k,b]))[1]
    bg_alone=g.rhs(np.stack([b]))[0]
    uK=g.inv(g.velocity(k));wB=g.inv(b)
    cross=g.curl(g.fwd(np.cross(uK,wB,axis=0)))
    err=np.linalg.norm((coupled-bg_alone-cross).ravel())
    assert err/max(np.linalg.norm(cross.ravel()),1e-30) < 1e-11
