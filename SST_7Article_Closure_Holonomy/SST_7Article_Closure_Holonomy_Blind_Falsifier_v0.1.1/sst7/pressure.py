from __future__ import annotations
import numpy as np

def _spacing(dx):
    a=np.asarray(dx,float).reshape(-1)
    if len(a)==1: return np.repeat(a,3)
    if len(a)!=3: raise ValueError('dx must be scalar or length 3')
    return a

def deriv(f,axis,h,periodic):
    if periodic:
        return (np.roll(f,-1,axis=axis)-np.roll(f,1,axis=axis))/(2*h)
    return np.gradient(f,h,axis=axis,edge_order=2)

def second(f,axis,h,periodic):
    if periodic:
        return (np.roll(f,-1,axis=axis)-2*f+np.roll(f,1,axis=axis))/(h*h)
    return np.gradient(np.gradient(f,h,axis=axis,edge_order=2),h,axis=axis,edge_order=2)

def invariants(v,dx,boundary='nonperiodic'):
    v=np.asarray(v,float)
    if v.ndim!=4 or v.shape[-1]!=3: raise ValueError('v must be (Nx,Ny,Nz,3)')
    h=_spacing(dx); periodic=str(boundary).lower()=='periodic'
    A=np.empty(v.shape[:-1]+(3,3),float)
    for i in range(3):
        for j in range(3): A[...,i,j]=deriv(v[...,i],j,h[j],periodic)
    S=0.5*(A+np.swapaxes(A,-1,-2))
    omega=np.empty(v.shape[:-1]+(3,),float)
    omega[...,0]=A[...,2,1]-A[...,1,2]
    omega[...,1]=A[...,0,2]-A[...,2,0]
    omega[...,2]=A[...,1,0]-A[...,0,1]
    source=0.5*np.sum(omega*omega,axis=-1)-np.sum(S*S,axis=(-2,-1))
    div=A[...,0,0]+A[...,1,1]+A[...,2,2]
    return source,div,omega,S

def laplacian(f,dx,boundary='nonperiodic'):
    h=_spacing(dx); periodic=str(boundary).lower()=='periodic'
    return sum(second(f,j,h[j],periodic) for j in range(3))

def poisson_residual(v,p,dx,rho,boundary='nonperiodic'):
    source,div,omega,S=invariants(v,dx,boundary)
    pi=np.asarray(p,float)/float(rho)
    lap=laplacian(pi,dx,boundary)
    num=np.linalg.norm((lap-source).ravel())
    den=np.linalg.norm(source.ravel())+1e-300
    drel=np.linalg.norm(div.ravel())/(np.linalg.norm(np.asarray(v).ravel())/max(_spacing(dx).mean(),1e-300)+1e-300)
    qomega=0.5*np.sum(omega*omega,axis=-1)
    qstrain=np.sum(S*S,axis=(-2,-1))
    return {
        'relative':float(num/den),
        'div_relative':float(drel),
        'source':source,
        'pi':pi,
        'qomega':qomega,
        'qstrain':qstrain,
        'qomega_l2':float(np.linalg.norm(qomega.ravel())),
        'qstrain_l2':float(np.linalg.norm(qstrain.ravel())),
        'source_l2':float(np.linalg.norm(source.ravel())),
        'vorticity_dominated_fraction':float(np.mean(source>0)),
    }

def periodic_green_reconstruct(source,dx):
    source=np.asarray(source,float); h=_spacing(dx)
    ks=[2*np.pi*np.fft.fftfreq(source.shape[i],d=h[i]) for i in range(3)]
    K=np.meshgrid(*ks,indexing='ij')
    k2=K[0]**2+K[1]**2+K[2]**2
    sh=np.fft.fftn(source-source.mean())
    ph=np.zeros_like(sh,dtype=complex)
    mask=k2>0
    ph[mask]=-sh[mask]/k2[mask]
    return np.fft.ifftn(ph).real

def green_relative(source,pi,dx):
    rec=periodic_green_reconstruct(source,dx)
    target=np.asarray(pi,float)-np.asarray(pi,float).mean()
    # allow a tiny global discretization mismatch but no arbitrary fit scale
    return float(np.linalg.norm((rec-target).ravel())/(np.linalg.norm(target.ravel())+1e-300))
