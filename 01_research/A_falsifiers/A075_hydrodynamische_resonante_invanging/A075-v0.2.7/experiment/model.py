"""Two fully back-reacting regularized centerline rings; NOT full 3D Euler.

All numerical quantities are expressed in normalized SI-compatible units
Gamma=1 m^2/s, rho=1 kg/m^3, reference length=1 m.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from math import pi

@dataclass(frozen=True)
class Case:
    n: int=24
    dt: float=0.05
    final_time: float=1.0
    a: float=0.22
    zsep: float=0.7
    gamma_receiver: float=1.0
    gamma_incoming: float=1.0

def initialize(n: int,zsep:float=0.7):
    th=np.arange(n,dtype=np.float64)*(2*pi/n)
    def circ(r,z):return np.column_stack((r*np.cos(th),r*np.sin(th),np.full_like(th,z)))
    return np.stack([circ(1.0,0.0),circ(0.82,zsep)])

def segments(x):
    x2=np.roll(x,-1,axis=1)
    return (x+x2)*0.5, x2-x

def velocities(x,gammas,a):
    n=x.shape[1]; mids,dl=segments(x)
    src_m=mids.reshape(2*n,3); src_d=dl.reshape(2*n,3)
    src_g=np.repeat(np.asarray(gammas,dtype=float),n)
    targets=x.reshape(2*n,3)
    d=targets[:,None,:]-src_m[None,:,:]
    inv=np.power(np.einsum('ijk,ijk->ij',d,d)+a*a,-1.5)
    cross=np.cross(src_d[None,:,:],d)
    v=np.sum(cross*inv[:,:,None]*src_g[None,:,None],axis=1)/(4*pi)
    return v.reshape(x.shape)

def hamiltonian_parts(x,gammas,a,rho=1.):
    n=x.shape[1]; mids,dl=segments(x)
    m=mids.reshape(2*n,3); d=dl.reshape(2*n,3)
    dr=m[:,None,:]-m[None,:,:]
    inv=1/np.sqrt(np.einsum('ijk,ijk->ij',dr,dr)+a*a)
    t=np.einsum('ic,jc->ij',d,d)*inv
    s=rho/(8*pi)
    h00=s*gammas[0]**2*np.sum(t[:n,:n])
    h11=s*gammas[1]**2*np.sum(t[n:,n:])
    hcross=s*2*gammas[0]*gammas[1]*np.sum(t[:n,n:])
    return np.array([h00,h11,hcross],dtype=float)

def impulse(x,gammas,rho=1.):
    return 0.5*rho*np.sum(np.asarray(gammas)[:,None,None]*np.cross(x,np.roll(x,-1,axis=1)),axis=(0,1))

def rk4(x,dt,gamma,a):
    k1=velocities(x,gamma,a)
    k2=velocities(x+0.5*dt*k1,gamma,a)
    k3=velocities(x+0.5*dt*k2,gamma,a)
    k4=velocities(x+dt*k3,gamma,a)
    return x+(dt/6)*(k1+2*k2+2*k3+k4)

def run(case:Case):
    steps=round(case.final_time/case.dt)
    if not np.isclose(steps*case.dt,case.final_time,rtol=0,atol=1e-12):
        raise ValueError('fixed final time must be exact number of steps')
    x=initialize(case.n,case.zsep)
    gamma=(case.gamma_receiver,case.gamma_incoming)
    es=[]; impulses=[]; zmeans=[]; minseps=[]; snap=[]
    for step in range(steps+1):
        if step in {0,steps//4,steps//2,3*steps//4,steps}:
            e=hamiltonian_parts(x,gamma,case.a)
            im=impulse(x,gamma)
            es.append([step*case.dt,*e, float(sum(e))]);impulses.append([step*case.dt,*im])
            zmeans.append([step*case.dt,float(x[0,:,2].mean()),float(x[1,:,2].mean())])
            minseps.append([step*case.dt,float(np.min(np.linalg.norm(x[0,:,None,:]-x[1,None,:,:],axis=-1)))])
            snap.append(x.copy())
        if step<steps: x=rk4(x,case.dt,gamma,case.a)
        if not np.isfinite(x).all():raise FloatingPointError('nonfinite ring coordinate')
    E=np.asarray(es);P=np.asarray(impulses)
    drift=float(np.max(np.abs(E[:,-1]-E[0,-1]))/max(abs(E[0,-1]),1e-15))
    impulse_drift=float(np.max(np.linalg.norm(P[:,1:]-P[0,1:],axis=1))/max(np.linalg.norm(P[0,1:]),1e-15))
    data={'case':case.__dict__,'time_energy':E.tolist(),'time_impulse':P.tolist(),'mean_z':zmeans,'min_separation':minseps,'relative_energy_drift':drift,'relative_impulse_drift':impulse_drift,'receiver_self_energy_change':float(E[-1,1]-E[0,1]),'incoming_self_energy_change':float(E[-1,2]-E[0,2]),'cross_energy_initial':float(E[0,3]),'cross_energy_final':float(E[-1,3]),'initial_total_energy':float(E[0,4]),'final_total_energy':float(E[-1,4]),'scope':'MIDPOINT_REGULARIZED_FILAMENT_NOT_EULER_CLOSURE'}
    return data, np.asarray(snap)

