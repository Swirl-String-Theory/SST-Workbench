import numpy as np
from . import _native
from .spectral import wave_numbers,project_hat,dealias_mask,velocity_from_vorticity


def base_trefoil(N,L,R,r,sigma,M=192):
    omega=np.asarray(_native.trefoil_vorticity_seed(N,L,R,r,sigma,M,1.0))
    uh=velocity_from_vorticity(omega,L)
    kx,ky,kz,k2=wave_numbers(N,L)
    mask=dealias_mask(N,kx,ky,kz)
    uh*=mask[None,...]
    # Normalize to unit RMS speed: all blind evolution is dimensionless.
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    rms=np.sqrt(np.mean(np.sum(u*u,axis=0)))
    return uh/rms


def localized_packet(uh,L,epsilon,kvec,avec,x0,sigma):
    N=uh.shape[1]; dx=L/N
    q=-0.5*L+(np.arange(N)+0.5)*dx
    X,Y,Z=np.meshgrid(q,q,q,indexing="ij")
    d=[(X-x0[0]+0.5*L)%L-0.5*L,(Y-x0[1]+0.5*L)%L-0.5*L,(Z-x0[2]+0.5*L)%L-0.5*L]
    env=np.exp(-(d[0]**2+d[1]**2+d[2]**2)/(2*sigma*sigma))
    phase=kvec[0]*d[0]+kvec[1]*d[1]+kvec[2]*d[2]
    # Vector potential A = a * env*cos(phase); curl(A) is divergence-free after spectral derivative.
    A=np.stack([avec[c]*env*np.cos(phase) for c in range(3)],axis=0)
    Ah=np.fft.fftn(A,axes=(1,2,3))
    kx,ky,kz,k2=wave_numbers(N,L)
    ph=np.empty_like(Ah)
    ph[0]=1j*(ky*Ah[2]-kz*Ah[1]); ph[1]=1j*(kz*Ah[0]-kx*Ah[2]); ph[2]=1j*(kx*Ah[1]-ky*Ah[0])
    ph=project_hat(ph,kx,ky,kz,k2)
    mask=dealias_mask(N,kx,ky,kz); ph*=mask[None,...]
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    p=np.fft.ifftn(ph,axes=(1,2,3)).real
    ur=np.sqrt(np.mean(np.sum(u*u,axis=0))); pr=np.sqrt(np.mean(np.sum(p*p,axis=0)))
    if pr==0: return uh.copy()
    return uh + (epsilon*ur/pr)*ph
