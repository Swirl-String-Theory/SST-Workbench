"""Fully 3D periodic GP stepping kernel, calibration controls only.

NO 3D trefoil initializer is admitted in v0.4.0. A complex field built from
nearest points on a curve is not generally a well-defined quantized vortex.
"""
from __future__ import annotations
import numpy as np

def gp_step(psi,dt,dx):
    """Dimensionless i psi_t=-1/2 Delta psi+(|psi|^2-1)psi."""
    if psi.ndim!=3 or any(n<8 or n%2 for n in psi.shape):raise ValueError('even dimensions >=8 required')
    if dt<=0 or dx<=0:raise ValueError('positive dt and dx')
    out=psi*np.exp(-.5j*dt*(np.abs(psi)**2-1))
    w=[2*np.pi*np.fft.fftfreq(n,d=dx) for n in out.shape]
    k2=sum(m*m for m in np.meshgrid(*w,indexing='ij'))
    out=np.fft.ifftn(np.fft.fftn(out)*np.exp(-.5j*dt*k2))
    return out*np.exp(-.5j*dt*(np.abs(out)**2-1))

def gp_energy(psi,dx):
    w=[2*np.pi*np.fft.fftfreq(n,d=dx) for n in psi.shape]
    z=np.fft.fftn(psi)
    gradenergy=sum(np.mean(np.abs(np.fft.ifftn(1j*w[j].reshape([1 if k!=j else psi.shape[j] for k in range(3)])*z))**2) for j in range(3))
    densityenergy=np.mean((np.abs(psi)**2-1)**2)
    return float(psi.size*dx**3*(.5*gradenergy+.5*densityenergy))

def reference_suite():
    """Exact plane wave benchmark: tests a 3D integrator, not a trefoil!"""
    n=16;dx=2*np.pi/n;z=np.arange(n)*dx
    psi=np.exp(1j*2*z)[:,None,None]*np.ones((1,n,n),complex)
    e0=gp_energy(psi,dx);n0=float(np.sum(abs(psi)**2)*dx**3)
    dt=.001;steps=20
    for _ in range(steps):psi=gp_step(psi,dt,dx)
    expect=np.exp(1j*2*z)[:,None,None]*np.ones((1,n,n))*np.exp(-1j*2*steps*dt)
    err=float(np.max(np.abs(psi-expect)))
    return {'schema':'A069-GP3D-REFERENCE-1','status':'PASS' if err<1e-11 else 'FAIL',
       'test':'periodic_plane_wave_k=2','max_complex_error':err,
       'mass_relative_drift':float(abs(np.sum(abs(psi)**2)*dx**3-n0)/n0),
       'energy_relative_drift':float(abs(gp_energy(psi,dx)-e0)/e0),
       'knotted_field_constructed':False,'physical_clock_prediction':False,
       'classification':'REFERENCE_ONLY'}
