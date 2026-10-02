import numpy as np
from sst_bkm.spectral import wave_numbers,project_hat,dealias_mask,rhs
from sst_bkm import _native


def test_native_seed_shape():
    w=np.asarray(_native.trefoil_vorticity_seed(12,2*np.pi,1.0,0.4,0.5,32,1.0))
    assert w.shape==(3,12,12,12)
    assert np.isfinite(w).all()


def test_projection_divergence():
    N=12; L=2*np.pi; rng=np.random.default_rng(2)
    v=rng.normal(size=(3,N,N,N)); vh=np.fft.fftn(v,axes=(1,2,3))
    kx,ky,kz,k2=wave_numbers(N,L); ph=project_hat(vh,kx,ky,kz,k2)
    divh=1j*(kx*ph[0]+ky*ph[1]+kz*ph[2])
    div=np.fft.ifftn(divh).real
    assert np.sqrt(np.mean(div*div))<1e-12


def test_beltrami_abc_rhs_small():
    N=16; L=2*np.pi
    x=np.arange(N)*L/N; X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    u=np.empty((3,N,N,N));
    u[0]=np.sin(Z)+np.cos(Y); u[1]=np.sin(X)+np.cos(Z); u[2]=np.sin(Y)+np.cos(X)
    uh=np.fft.fftn(u,axes=(1,2,3)); kx,ky,kz,k2=wave_numbers(N,L); uh=project_hat(uh,kx,ky,kz,k2)
    mask=dealias_mask(N,kx,ky,kz)
    rh=rhs(uh,L,mask); scale=np.max(np.abs(uh))
    assert np.max(np.abs(rh))/scale<1e-12
