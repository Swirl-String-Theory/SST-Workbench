"""Exact linear Hamiltonian two-mode testbed. Not a 3D Euler solver."""
import numpy as np


def evolve(q0, v0, t, omega_k=2.0, omega_b=3.1, coupling=2.0):
    K = np.array([[omega_k**2, coupling], [coupling, omega_b**2]], dtype=float)
    eig, U = np.linalg.eigh(K)
    if np.min(eig) <= 0:
        raise ValueError('unstable benchmark potential')
    w = np.sqrt(eig)
    q0 = np.asarray(q0, dtype=float)
    v0 = np.asarray(v0, dtype=float)
    qh = q0 @ U
    vh = v0 @ U
    q = (qh * np.cos(w*t) + vh * np.sin(w*t)/w) @ U.T
    v = (-qh * w*np.sin(w*t) + vh*np.cos(w*t)) @ U.T
    return q, v


def energy(q, v, omega_k=2.0, omega_b=3.1, coupling=2.0, mass_kg=1.0):
    """Conserved energy in joules for q in metres and t in seconds."""
    return mass_kg*0.5*(np.sum(v*v,axis=-1) + omega_k**2*q[...,0]**2 + omega_b**2*q[...,1]**2 + 2*coupling*q[...,0]*q[...,1])


def synthetic(n=1500, seed=20261029, coupling=2.0, delay_s=0.65, horizon_s=0.75, noise_m=2e-4):
    rng=np.random.default_rng(seed)
    q0=rng.normal(0, 0.01,(n,2)); v0=rng.normal(0,0.02,(n,2))
    earlier=2.1-delay_s
    if earlier < 0: raise ValueError('delay too large')
    qp,vp=evolve(q0,v0,earlier,coupling=coupling)
    qc,vc=evolve(q0,v0,2.1,coupling=coupling)
    qf,vf=evolve(q0,v0,2.1+horizon_s,coupling=coupling)
    target=qf[:,0]+rng.normal(0,noise_m,n)
    return {'current':np.column_stack((qc[:,0],vc[:,0])),
            'history':np.column_stack((qp[:,0],vp[:,0])),
            'full':np.column_stack((qc[:,0],vc[:,0],qc[:,1],vc[:,1])),
            'target':target, 'q0':q0, 'v0':v0,
            'initial_energy':energy(q0,v0), 'final_energy':energy(qf,vf),
            'units':{'q':'m','qdot':'m/s','t':'s','energy':'J'}}
