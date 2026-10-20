"""Configurable-coupling 3D Hamiltonian GP, with explicit core-scale contract.

Normalized GP: i Psi_T = -(1/2) ∇² Psi + μ(|Psi|²-1) Psi.
An exact *planar* black soliton has f(x) = tanh(sqrt(μ) x), so for the
initializer f=tanh(d/(sqrt(2)*xi)), require μ=1/(2 xi²).
This is a useful preparation consistency condition, NOT a theorem that a
knotted 3D vortex core is stationary, nor a derived SST-Euler core.
Changing μ changes the physical GP model; xi sweeps are model sensitivity,
not pure mesh convergence.
"""
from __future__ import annotations
from functools import lru_cache
import numpy as np


def coupling_from_xi(xi:float)->float:
    if xi<=0:raise ValueError('xi>0 required')
    return 1.0/(2.0*xi*xi)


@lru_cache(maxsize=6)
def kinetic(n:int,box:float,dt:float):
    k=2*np.pi*np.fft.fftfreq(n,d=box/n)
    return np.exp(-.5j*dt*(k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2))


def step_mu(psi:np.ndarray,box:float,dt:float,mu:float,kin=None):
    if mu<=0 or dt<=0:raise ValueError('mu,dt>0 required')
    if kin is None:kin=kinetic(psi.shape[0],box,dt)
    z=psi*np.exp(-.5j*dt*mu*(abs(psi)**2-1))
    z=np.fft.ifftn(np.fft.fftn(z)*kin)
    return z*np.exp(-.5j*dt*mu*(abs(z)**2-1))


def conserved_mu(psi:np.ndarray,box:float,mu:float):
    if mu<=0:raise ValueError('mu>0 required')
    n=len(psi); k=2*np.pi*np.fft.fftfreq(n,d=box/n)
    z=np.fft.fftn(psi)
    grad2=0.
    for axis in range(3):
        sh=[1,1,1];sh[axis]=n
        grad2+=np.mean(abs(np.fft.ifftn(z*(1j*k.reshape(sh))))**2)
    return float(np.mean(abs(psi)**2)*box**3),float((.5*grad2+.5*mu*np.mean((abs(psi)**2-1)**2))*box**3)


def planar_soliton_residual(x,xi):
    """Explicit analytic residual -f''/2 + μ(f²-1)f = 0."""
    mu=coupling_from_xi(xi);a=np.sqrt(mu);f=np.tanh(a*np.asarray(x))
    second=-2*a*a*f*(1-f*f)
    return -.5*second+mu*(f*f-1)*f
