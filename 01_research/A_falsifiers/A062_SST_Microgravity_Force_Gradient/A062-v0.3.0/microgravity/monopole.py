"""A062-v0.3: conditional *postulated* scalar EFT. No physical SST monopole is derived here.
Dimensionless H1: perimeter=1, q_i=ds_i/L, kappa=lambda=1; force reported in Q_A Q_B/(4pi L^2) units.
"""
import numpy as np
from .filament import rotate_x

def weights(x):
    dl=np.roll(x,-1,axis=0)-x; ll=np.linalg.norm(dl,axis=1)
    return (x+0.5*dl),ll/ll.sum()

def source_gradient(pts,x,softening=0.,block=400):
    center,w=weights(x); pts=np.asarray(pts,dtype=float); ans=np.empty_like(pts)
    for k in range(0,len(pts),block):
        v=pts[k:k+block,None,:]-center[None,:,:]
        d=(v*v).sum(axis=2)+softening**2
        ans[k:k+block]=-(v*(w[None,:,None]/d[:,:,None]**1.5)).sum(axis=1)/(4*np.pi)
    return ans

def source_potential(pts,x,softening=0.,block=400):
    center,w=weights(x);pts=np.asarray(pts,float);ans=np.empty(len(pts))
    for k in range(0,len(pts),block):
        v=pts[k:k+block,None,:]-center[None,:,:]
        ans[k:k+block]=(w[None,:]/np.sqrt((v*v).sum(axis=2)+softening**2)).sum(axis=1)/(4*np.pi)
    return ans

def force(xa,xb,R,theta=0,epsilon=0.):
    """Attractive test-body force from *assumed* L_int=-lambda q tau."""
    b=rotate_x(xb,theta)+np.array([0.,0.,R])
    pts,w=weights(b)
    return (source_gradient(pts,xa,epsilon)*w[:,None]).sum(axis=0)

def force_pair(xa,xb,R,theta=0,epsilon=0.):
    b=rotate_x(xb,theta)+[0,0,R]
    f=force(xa,xb,R,theta,epsilon)
    # swapping sources B and A, force on A is opposite
    pts,w=weights(xa)
    fa=(source_gradient(pts,b,epsilon)*w[:,None]).sum(axis=0)
    return f,fa

def fit_slope(xa,xb,distances=(8,12,18,27,40),epsilon=0.):
    z=np.array([force(xa,xb,R,epsilon=epsilon)[2] for R in distances])
    return float(-np.polyfit(np.log(distances),np.log(abs(z)),1)[0]),z

def fibonacci_sphere(n):
    k=np.arange(n,dtype=float)+.5
    z=1-2*k/n; phi=k*np.pi*(3-np.sqrt(5));r=np.sqrt(1-z*z)
    return np.c_[r*np.cos(phi),r*np.sin(phi),z]

def cross_stress_integral(xa,xb,R,theta=0.,epsilon=0.,nsurf=900,radius=.32):
    """Interaction-part scalar stress across sphere around B.
    Does NOT establish fluid Euler momentum force. Sign convention recorded separately.
    """
    b=rotate_x(xb,theta)+[0,0,R]; n=fibonacci_sphere(nsurf)
    pts=n*radius + np.array([0,0,R])
    gA=source_gradient(pts,xa,epsilon);gB=source_gradient(pts,b,epsilon)
    T=np.einsum('ni,nj->nij',gA,gB)+np.einsum('ni,nj->nij',gB,gA)-np.einsum('n,ij->nij',np.einsum('ni,ni->n',gA,gB),np.eye(3))
    return np.einsum('nij,nj->i',T,n)*4*np.pi*radius**2/nsurf

def euler_pressure_monopole_analytic(x):
    """Localized incompressible field p-source = -rho * double divergence(v_i v_j).
    Volume monopole must vanish if the flux at infinity vanishes.
    This is a structural identity, not a sampled pressure field.
    """
    return 0.0
