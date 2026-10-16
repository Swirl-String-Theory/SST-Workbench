"""Matrix-free eigenpairs of the *actual frozen* tangent Euler-Galerkin operator.
Not a Kelvin-wave eigenproblem unless background is a relative equilibrium.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse.linalg import LinearOperator, eigs
from euler_tangent import Euler3D, load_geometry, normalized_components

def operator(grid: Euler3D,U):
    U=grid.project(U)
    vort=grid.curl(U)
    shape=U.shape
    def apply_real(f):
        d=grid.project(np.asarray(f,dtype=float).reshape(shape))
        return grid.project(grid.cross(d,vort)+grid.cross(U,grid.curl(d)))
    def matvec(v):
        v=np.asarray(v)
        if np.iscomplexobj(v): return (apply_real(v.real)+1j*apply_real(v.imag)).ravel()
        return apply_real(v).ravel()
    return LinearOperator((U.size,U.size),matvec=matvec,dtype=np.float64),apply_real

def finite_difference_check(g,U,D,epsilon=1e-5):
    # Directional derivative for the actual Euler nonlinear RHS.
    Np,_=g.rhs(U+epsilon*D,np.empty((0,*U.shape)))
    Nm,_=g.rhs(U-epsilon*D,np.empty((0,*U.shape)))
    Lop=operator(g,U)[1](D)
    return float(np.linalg.norm((Np-Nm)/(2*epsilon)-Lop)/(np.linalg.norm(Lop)+1e-30))

def compute_spectrum(path,n=12,core=.4,nev=4,seed=44064,dt=.04,t_eval=.8):
    geom,sha=load_geometry(path)
    g=Euler3D(n,core)
    U=g.velocity_from_curve(normalized_components(geom)[0]); op,apply=operator(g,U)
    rng=np.random.default_rng(seed)
    v0=g.project(rng.normal(size=U.shape)); v0=v0.ravel()
    vals,vec=eigs(op,k=nev,which='LR',tol=1e-8,ncv=max(24,4*nev+4),maxiter=1400,v0=v0)
    candidates=[]
    for j,(lam,vec0) in enumerate(zip(vals,vec.T)):
        residual=np.linalg.norm(op@vec0-lam*vec0)/(np.linalg.norm(op@vec0)+abs(lam)*np.linalg.norm(vec0)+1e-30)
        div=max(g.divergence_relative(vec0.real.reshape(U.shape)),g.divergence_relative(vec0.imag.reshape(U.shape)))
        candidates.append(dict(real=float(lam.real),imag=float(lam.imag),abs=float(abs(lam)),
                               relative_residual=float(residual),divergence_relative=float(div)))
    # Baseline is not stationary; frozen-operator eigenvectors are not modes of full U(t).
    dU,_=g.rhs(U,np.empty((0,*U.shape)))
    nonstationary_rate=float(np.linalg.norm(dU)/(np.linalg.norm(U)+1e-30))
    # Change of the same frozen linear operator after evolving U.
    Uf=U.copy()
    for _ in range(round(t_eval/dt)):
        Uf,_=g.rk4(Uf,np.empty((0,*U.shape)),dt)
    opf,_=operator(g,Uf)
    v=vec[:,0]
    operator_variation=float(np.linalg.norm(opf@v-op@v)/(np.linalg.norm(op@v)+1e-30))
    return dict(source_sha256=sha,grid=n,core=core,operator='P[(d x curl(U)) + (U x curl(d))]',
                frozen_time=0.,probe_time=t_eval,
                nonstationary_rate=nonstationary_rate,finite_time_operator_variation=operator_variation,
                candidates=candidates,
                scientific_status='INSTANTANEOUS_EULER_GALERKIN_EIGENVECTORS__KELVIN_MODE_UNQUALIFIED')
