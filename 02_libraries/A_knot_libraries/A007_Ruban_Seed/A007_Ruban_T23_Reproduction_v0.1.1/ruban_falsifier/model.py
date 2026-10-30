"""Ruban 2018 equation (9) in R0=1, Gamma=2*pi dimensionless units.

Reference: https://arxiv.org/pdf/1801.04822 (eqs 6-9).
The regularization delta IS NOT the physical core xi. The local coefficient
lambda_tilde=Lambda+ln(delta) supplies the compensating induction term.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit

TWOPI=2*math.pi

def torus_knot(n:int, b0:float, p:int=2, q:int=3, phase:float=0., perturbation:float=0., seed:int=20261030)->np.ndarray:
    """Ruban 1806.10783 eqs (1-3) for n=1, p=2, q=3, Theta0=0.
    Perturbation is deterministic smooth Fourier noise; source is unperturbed
    analytic geometry, not interpolation of the VortexLab XYZ file.
    """
    if n < 24 or math.gcd(p,q)!=1 or not 0 < b0 < 0.5:
        raise ValueError('invalid torus seed parameters')
    beta=TWOPI*np.arange(n)/n
    th=q*beta+phase
    r=1+b0*np.sin(th)
    x=np.column_stack((r*np.cos(p*beta),r*np.sin(p*beta),b0*np.cos(th)))
    if perturbation:
        rng=np.random.default_rng(seed)
        # Common smooth, not point-wise random modes to avoid UV-dominated noise.
        modes=rng.normal(size=(3,3,2))
        noise=np.zeros_like(x)
        for mode in range(1,4):
            noise+=modes[mode-1,:,0][None,:]*np.sin(mode*beta)[:,None]/mode**2
            noise+=modes[mode-1,:,1][None,:]*np.cos(mode*beta)[:,None]/mode**2
        noise/=max(np.sqrt(np.mean(np.sum(noise*noise,axis=1))),1e-30)
        x+=perturbation*noise
    return np.ascontiguousarray(x,dtype=np.float64)

def ring(n:int, radius:float=1.)->np.ndarray:
    b=TWOPI*np.arange(n)/n
    return np.column_stack((radius*np.cos(b),radius*np.sin(b),np.zeros(n)))

def derivatives(x:np.ndarray)->tuple[np.ndarray,np.ndarray]:
    n=len(x)
    k=np.fft.fftfreq(n,d=1/n)
    X=np.fft.fft(x,axis=0)
    # Nyquist first derivative is non-unique for a real sampled function.
    k1=k.copy()
    if n%2==0: k1[n//2]=0.
    xp=np.fft.ifft((1j*k1)[:,None]*X,axis=0).real
    xpp=np.fft.ifft((-(k*k))[:,None]*X,axis=0).real
    return xp,xpp

@njit(cache=True)
def _integral(x, xp, delta):
    n=x.shape[0]
    result=np.zeros((n,3),dtype=np.float64)
    d2=delta*delta
    quadrature=TWOPI/n
    for i in range(n):
        s0=s1=s2=0.0
        xi=x[i,0]; yi=x[i,1]; zi=x[i,2]
        for j in range(n):
            dx=xi-x[j,0];dy=yi-x[j,1];dz=zi-x[j,2]
            w=1.0/((dx*dx+dy*dy+dz*dz+d2)**1.5)
            s0+=(xp[j,1]*dz-xp[j,2]*dy)*w
            s1+=(xp[j,2]*dx-xp[j,0]*dz)*w
            s2+=(xp[j,0]*dy-xp[j,1]*dx)*w
        result[i,0]=0.5*quadrature*s0
        result[i,1]=0.5*quadrature*s1
        result[i,2]=0.5*quadrature*s2
    return result

@njit(cache=True)
def _hamiltonian(x,xp,delta,lt):
    n=x.shape[0];d2=delta*delta; s=0.0;length=0.0
    for i in range(n):
        length+=math.sqrt(np.dot(xp[i],xp[i]))
        for j in range(n):
            dx=x[i,0]-x[j,0];dy=x[i,1]-x[j,1];dz=x[i,2]-x[j,2]
            s+=np.dot(xp[i],xp[j])/math.sqrt(dx*dx+dy*dy+dz*dz+d2)
    quadrature=TWOPI/n
    # H for rho=1, Gamma=2*pi: kinetic=pi/2 * double integral,
    # potential=pi*lt * single integral of |X'|.
    return (math.pi/2)*s*quadrature**2 + math.pi*lt*length*quadrature

class RubanModel:
    def __init__(self, Lambda:float=1.4+0.5*math.log(200),delta:float=0.05,include_local:bool=True):
        if delta<=0 or not np.isfinite(delta) or not np.isfinite(Lambda): raise ValueError('invalid Lambda/delta')
        self.Lambda=float(Lambda)
        self.delta=float(delta)
        self.lambda_tilde=float(Lambda+math.log(delta))
        self.include_local=bool(include_local)
    def velocity(self,x:np.ndarray)->np.ndarray:
        xp,xpp=derivatives(x)
        u=_integral(np.ascontiguousarray(x),np.ascontiguousarray(xp),self.delta)
        if self.include_local:
            cb=np.cross(xp,xpp)/np.maximum(np.linalg.norm(xp,axis=1)**3,1e-25)[:,None]
            u+=0.5*self.lambda_tilde*cb
        if not np.all(np.isfinite(u)): raise FloatingPointError('non-finite velocity')
        return u
    def energy(self,x:np.ndarray)->float:
        xp,_=derivatives(x)
        return float(_hamiltonian(np.ascontiguousarray(x),np.ascontiguousarray(xp),self.delta,
             self.lambda_tilde if self.include_local else 0.0))
    def rk4(self,x:np.ndarray,dt:float)->np.ndarray:
        k1=self.velocity(x)
        k2=self.velocity(x+0.5*dt*k1)
        k3=self.velocity(x+0.5*dt*k2)
        k4=self.velocity(x+dt*k3)
        y=x+(dt/6)*(k1+2*k2+2*k3+k4)
        if not np.all(np.isfinite(y)): raise FloatingPointError('non-finite RK4 result')
        return y
