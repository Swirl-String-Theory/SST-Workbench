"""Source-traced, dimensionless analytical identities for A060 M01--M04.

No SST physical constants and no target-dependent calibration are present.
The functions are reference diagnostics, not a replacement for the v1.0.7 framework.
"""
from __future__ import annotations
import numpy as np


def landreman_field(x, eps=0.25):
    """Landreman (2026), equations (2.1)--(2.3), dimensionless coordinates."""
    x, y, z = np.asarray(x, dtype=float)
    if not (0 <= eps < 1):
        raise ValueError('0<=epsilon<1 required')
    a, b = np.sqrt(1+eps), np.sqrt(1-eps)
    s = x*x/(a*a) + y*y/(b*b)
    rad = 1-(1-s)**2-4*z*z
    if not (rad > 0 and s > 0):
        raise ValueError('point outside analytic toroidal region')
    F = np.sqrt(rad)
    return np.array([(2*z*x-a/b*F*y)/s, (2*z*y+b/a*F*x)/s, 1-s])


def landreman_kinematic_pressure(x):
    x, y, z = np.asarray(x, dtype=float)
    return 0.5*(x*x+y*y+4*z*z)


def finite_jacobian(fun, x, h=1e-5):
    x = np.asarray(x, dtype=float)
    A = np.zeros((3,3), dtype=float)
    for j in range(3):
        step = np.eye(3)[j]*h
        A[:,j] = (fun(x+step)-fun(x-step))/(2*h)
    return A


def vorticity_from_A(A):
    return np.array([A[2,1]-A[1,2], A[0,2]-A[2,0], A[1,0]-A[0,1]])


def diagnostics(A):
    A=np.asarray(A,dtype=float)
    if A.shape != (3,3):
        raise ValueError('3x3 only')
    n2=float(np.sum(A*A))
    if n2 == 0:
        raise ValueError('zero tensor: normalized invariants undefined')
    S=(A+A.T)/2
    w=vorticity_from_A(A)
    Q=-0.5*float(np.trace(A@A))
    R=-float(np.linalg.det(A))
    lam=np.linalg.eigvals(A)
    shearfrac=1-float(np.sum(np.abs(lam)**2))/n2
    qhat=Q/n2
    rhat=R/n2**1.5
    m=max(2*abs(qhat),(2*abs(rhat))**(2/3))
    chi=abs(0.5*np.dot(w,w)-np.sum(S*S))/n2
    va_prod=float(w@S@w)
    omega2=float(w@w)
    alpha=va_prod/omega2 if omega2 > 1e-24 else np.nan
    vt=S@w-(alpha*w if omega2 > 1e-24 else np.zeros(3))
    sing=np.linalg.svd(A,compute_uv=False)
    r1=1-float(sing[0]**2)/n2
    Rs=-float(np.trace(S@S@S))/3
    Vs=va_prod
    fluxfactor=3*Rs+Vs/4
    return dict(Q=Q,R=R,f=shearfrac,m=m,chi=chi,r1=r1,
                enstrophy_density=omega2/2,strain_sq=float(np.sum(S*S)),
                poisson_source=2*Q,alpha_va=alpha,vt=vt,
                Rs=Rs,Vs=Vs,fluxfactor=fluxfactor)


def rank_one(g=1.0):
    return np.array([[0.,g,0.],[0.,0.,0.],[0.,0.,0.]])


def rank_two(g=1.0,eps=0.0):
    return np.array([[0.,g,0.],[0.,0.,g],[eps,0.,0.]])


def balanced(a=1.0):
    return np.array([[-a/2,-np.sqrt(3)*a/2,0],
                     [np.sqrt(3)*a/2,-a/2,0],[0,0,a]])


def rank_one_gate(g=1.0, eps=0.01, sign=1):
    return np.array([[0.,g,0.],[sign*eps,0.,0.],[0.,0.,0.]])


def direct_spherical_flux(A, diameter=1.0, n_mu=12, n_phi=24):
    """Independent angle-integral of Zhang & Yao eq.(1) for a linear field.
    delta u = diameter*A*n, phi=-3/(4*diameter)<|delta u|^2 delta u.n>.
    Gauss-Legendre x equispaced azimuth quadrature integrates quartics exactly.
    """
    mu, weight = np.polynomial.legendre.leggauss(n_mu)
    phi=np.arange(n_phi)*(2*np.pi/n_phi)
    c=np.cos(phi)[None,:]; s=np.sin(phi)[None,:]
    st=np.sqrt(1-mu**2)[:,None]
    nv=np.stack(np.broadcast_arrays(st*c,st*s,mu[:,None]*np.ones_like(c)),axis=-1)
    d=diameter*np.einsum('ij,...j->...i',A,nv)
    term=np.sum(d*d,axis=-1)*np.sum(d*nv,axis=-1)
    return float(-3/(4*diameter)*np.sum(term*weight[:,None])/(2*n_phi))


def gradient_flux_prediction(A, diameter=1.0):
    return diameter**2/10*diagnostics(A)['fluxfactor']
