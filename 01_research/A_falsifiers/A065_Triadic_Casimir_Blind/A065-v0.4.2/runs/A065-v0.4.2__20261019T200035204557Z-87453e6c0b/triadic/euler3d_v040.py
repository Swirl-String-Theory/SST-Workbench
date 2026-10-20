"""Independent numerical 3-D incompressible Euler integrator (periodic Fourier/RK4).

Scientific scope: a genuine discretized Euler IVP, but NOT independent
source-native PKLSA physics. Initial u is imported from an assumed Gaussian
vortex tube or an explicitly labelled analytic Taylor-Green control.

Rotational form: du/dt = P[u x curl(u)]; div(u)=0.
Gauge pressure from Poisson: q=p/rho+|u|^2/2, Laplace(q)=div(u x omega).
All arrays float64; pressure periodic mean gauge zero. 2/3 truncation applied
in spectral RHS and at every RK4 stage. No viscosity or external forcing.
"""
from __future__ import annotations
import math
import numpy as np


def wave(n, L):
    k=2*np.pi*np.fft.fftfreq(n,d=L/n)
    K=np.array(np.meshgrid(k,k,k,indexing='ij'))
    k2=np.einsum('ixyz,ixyz->xyz',K,K)
    inv=np.zeros_like(k2); np.divide(1.,k2,out=inv,where=k2>0)
    modes=np.fft.fftfreq(n)*n
    ix,iy,iz=np.meshgrid(modes,modes,modes,indexing='ij')
    mask=(np.abs(ix)<n/3)&(np.abs(iy)<n/3)&(np.abs(iz)<n/3)
    return K,k2,inv,mask


def project(U,K,inv,mask):
    d=np.einsum('ixyz,ixyz->xyz',K,U)
    out=(U-K*(d*inv)[None])*mask[None]
    out[:,0,0,0]=0
    return out


def omega_from_uhat(U,K):
    return np.array([1j*(K[1]*U[2]-K[2]*U[1]),
                     1j*(K[2]*U[0]-K[0]*U[2]),
                     1j*(K[0]*U[1]-K[1]*U[0])])


def rhs_hat(U,K,inv,mask):
    u=np.fft.ifftn(U,axes=(-3,-2,-1)).real
    W=omega_from_uhat(U,K)
    w=np.fft.ifftn(W,axes=(-3,-2,-1)).real
    cross=np.cross(u,w,axis=0)
    C=np.fft.fftn(cross,axes=(-3,-2,-1))
    return project(C,K,inv,mask)


def integrate(u0,L,T=.02,steps=4,rho=1.):
    """Explicit no-fit numerical Euler path. Returns u/omega/p at T and audits."""
    if u0.ndim!=4 or u0.shape[0]!=3 or len(set(u0.shape[1:]))!=1 or steps<1 or T<=0:
        raise ValueError('INVALID_EULER_INPUT')
    n=u0.shape[1];K,k2,inv,mask=wave(n,L)
    U0=project(np.fft.fftn(u0,axes=(-3,-2,-1)),K,inv,mask)
    def invs(U):
        u=np.fft.ifftn(U,axes=(-3,-2,-1)).real
        w=np.fft.ifftn(omega_from_uhat(U,K),axes=(-3,-2,-1)).real
        E=float(.5*np.mean(np.sum(u*u,axis=0))*L**3)
        H=float(np.mean(np.sum(u*w,axis=0))*L**3)
        Z=float(.5*np.mean(np.sum(w*w,axis=0))*L**3)
        return E,H,Z
    start=invs(U0)
    U=U0.copy();dt=T/steps
    for _ in range(steps):
        k1=rhs_hat(U,K,inv,mask)
        k2h=rhs_hat(project(U+dt*k1/2,K,inv,mask),K,inv,mask)
        k3=rhs_hat(project(U+dt*k2h/2,K,inv,mask),K,inv,mask)
        k4=rhs_hat(project(U+dt*k3,K,inv,mask),K,inv,mask)
        U=project(U+(dt/6)*(k1+2*k2h+2*k3+k4),K,inv,mask)
    u=np.fft.ifftn(U,axes=(-3,-2,-1)).real
    omega=np.fft.ifftn(omega_from_uhat(U,K),axes=(-3,-2,-1)).real
    C=np.fft.fftn(np.cross(u,omega,axis=0),axes=(-3,-2,-1))
    # ∇²q = div(u×omega), q=p/rho+|u|²/2
    qhat=-1j*np.einsum('ixyz,ixyz->xyz',K,C)*inv
    qhat[0,0,0]=0
    q=np.fft.ifftn(qhat).real
    p=rho*(q-.5*np.sum(u*u,axis=0));p-=np.mean(p)
    div=np.fft.ifftn(1j*np.einsum('ixyz,ixyz->xyz',K,U)).real
    end=invs(U)
    curl_trust=np.fft.ifftn(omega_from_uhat(np.fft.fftn(u,axes=(-3,-2,-1)),K),axes=(-3,-2,-1)).real
    audit={'schema':'A065-EULER3D-NUMERICAL-1','solver':'Fourier pseudospectral Euler rotational RK4 2/3 de-alias, periodic',
      'n':n,'L':L,'T':T,'dt':dt,'steps':steps,'initial_energy':start[0],'final_energy':end[0],
      'relative_energy_drift':abs(end[0]-start[0])/max(start[0],1e-30),
      'initial_helicity':start[1],'final_helicity':end[1],
      'relative_helicity_drift':abs(end[1]-start[1])/max(abs(start[1]),1e-15),
      'initial_enstrophy':start[2],'final_enstrophy':end[2],
      'div_u_rms':float(np.sqrt(np.mean(div**2))),
      'curl_u_omega_relative':float(np.linalg.norm((curl_trust-omega).ravel())/max(np.linalg.norm(omega.ravel()),1e-30)),
      'source_class':'NUMERICAL_EULER_FROM_ASSUMED_INITIAL_DATA_NOT_SOURCE_NATIVE_PKLSA',
      'independent_physical_pressure_holdout':False}
    return {'u':u,'omega':omega,'p':p,'audit':audit}


def taylor_green(n=24,L=2*np.pi):
    x=(np.arange(n)-n//2)*L/n
    X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
    return np.array([np.sin(X)*np.cos(Y)*np.cos(Z),-np.cos(X)*np.sin(Y)*np.cos(Z),np.zeros_like(X)])
