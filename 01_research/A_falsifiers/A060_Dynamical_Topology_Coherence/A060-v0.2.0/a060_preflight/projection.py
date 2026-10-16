"""Periodic spectral demonstration of curl inverse-Laplacian VA projection."""
import numpy as np


def projection_demo(N=24):
    x=np.arange(N)*2*np.pi/N
    xx,yy,zz=np.meshgrid(x,x,x,indexing='ij')
    v=np.stack([np.sin(yy),np.sin(zz),np.sin(xx)],axis=-1)
    ks=np.fft.fftfreq(N,d=1/N)
    K=np.stack(np.meshgrid(ks,ks,ks,indexing='ij'),axis=-1)
    K2=np.sum(K*K,axis=-1)
    def dx(field):
        fft=np.fft.fftn(field,axes=(0,1,2))
        return np.stack([np.fft.ifftn(1j*K[...,j,None]*fft,axes=(0,1,2)).real for j in range(3)],axis=-1)
    def curl(F):
        D=dx(F)
        return np.stack([D[...,2,1]-D[...,1,2],D[...,0,2]-D[...,2,0],D[...,1,0]-D[...,0,1]],axis=-1)
    def div(F):
        D=dx(F)
        return D[...,0,0]+D[...,1,1]+D[...,2,2]
    def inverse_lap(F):
        spec=np.fft.fftn(F,axes=(0,1,2))
        w=np.where(K2>0,-1/np.where(K2>0,K2,1),0)
        return np.fft.ifftn(spec*(w[...,None] if F.ndim==4 else w),axes=(0,1,2)).real
    A=dx(v)
    w=curl(v)
    S=(A+np.swapaxes(A,-1,-2))/2
    Sw=np.einsum('...ij,...j->...i',S,w)
    ww=np.einsum('...i,...i->...',w,w)
    alpha=np.einsum('...i,...i->...',w,Sw)/np.maximum(ww,1e-20)
    VA=alpha[...,None]*w
    divergence=div(VA)
    phi=inverse_lap(divergence)
    gradphi=dx(phi[...,None])[...,0,:]
    PVA=VA-gradphi
    PVA=PVA-np.mean(PVA,axis=(0,1,2),keepdims=True) # curl-invertible zero-mean sector
    g=inverse_lap(curl(VA))
    minus_PVA=curl(g)
    identity_error=float(np.max(np.abs(minus_PVA+PVA)))
    div_error=float(np.max(np.abs(div(PVA))))
    global_enstrophy=float(np.mean(np.einsum('...i,...i->...',w,gradphi)))
    return {'projection_curl_error':identity_error,'divergence_projected_va':div_error,
            'non_solenoidal_va_max':float(np.max(np.abs(divergence))),
            'mean_omega_gradphi':global_enstrophy,
            'local_omega_gradphi_max':float(np.max(np.abs(np.sum(w*gradphi,axis=-1))))}
