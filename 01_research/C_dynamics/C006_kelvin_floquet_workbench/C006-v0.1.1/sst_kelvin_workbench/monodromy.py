"""True relative-return Floquet monodromy for an accepted RPO.

Unlike v0.3's frozen local generator, this differentiates the *time-T nonlinear
flow map* along the full evolved orbit.  The relative group element g determined
by the unperturbed RPO is held fixed, as required for D(g^{-1} o phi_T).

For scientific honesty the full-state finite-difference monodromy is restricted to
small N by default.  It is never evaluated when the RPO gate is closed.
"""
from __future__ import annotations
import math
from typing import Any
import numpy as np

from .backend import load_backend
from .dynamics import kelvin_template, embed_transverse
from .geometry import bishop_frame
from .orbit import pair_rhs_hat, rk4_step, apply_common_shift


def integrate_to_period(state0: np.ndarray, *, period_hat: float, dt_hat: float, rhs) -> np.ndarray:
    nsteps=max(1,int(math.ceil(period_hat/dt_hat)))
    h=period_hat/nsteps
    x=np.asarray(state0,dtype=float).copy()
    for _ in range(nsteps):
        x=rk4_step(x,h,rhs)
    return x


def fixed_relative_map_terminal(xT: np.ndarray, *, shift: int, rotation: np.ndarray,
                                translation: np.ndarray) -> np.ndarray:
    s=apply_common_shift(xT,shift)
    return s@np.asarray(rotation,dtype=float)+np.asarray(translation,dtype=float)


def full_relative_monodromy_fd(state0: np.ndarray, *, D: float, period_hat: float, dt_hat: float,
                               shift: int, rotation: np.ndarray, translation: np.ndarray,
                               eps_over_D: float, gamma_plus: float=1.0, gamma_minus: float=-1.0,
                               fd_step_over_D: float=2e-5, max_n: int=24,
                               force_python: bool=False, skip_build: bool=False) -> dict[str,Any]:
    x0=np.asarray(state0,dtype=float)
    if x0.shape[0]!=2 or x0.shape[2]!=3: raise ValueError("state0 must be (2,N,3)")
    N=x0.shape[1]
    if N>max_n:
        raise ValueError(f"full monodromy intentionally limited to N<={max_n}; got N={N}")
    backend,bname=load_backend(force_python=force_python,skip_build=skip_build)
    rhs=lambda x: pair_rhs_hat(x,D=D,gamma_plus=gamma_plus,gamma_minus=gamma_minus,
                               eps_over_D=eps_over_D,backend=backend)
    baseT=integrate_to_period(x0,period_hat=period_hat,dt_hat=dt_hat,rhs=rhs)
    baseR=fixed_relative_map_terminal(baseT,shift=shift,rotation=rotation,translation=translation)
    base_res=float(np.linalg.norm(baseR-x0)/max(np.linalg.norm(x0-x0.mean(axis=(0,1))),1e-30))
    dim=x0.size; delta=fd_step_over_D*D
    M=np.empty((dim,dim),dtype=float)
    for j in range(dim):
        e=np.zeros(dim,dtype=float); e[j]=delta
        xp=(x0.reshape(-1)+e).reshape(x0.shape); xm=(x0.reshape(-1)-e).reshape(x0.shape)
        pT=integrate_to_period(xp,period_hat=period_hat,dt_hat=dt_hat,rhs=rhs)
        mT=integrate_to_period(xm,period_hat=period_hat,dt_hat=dt_hat,rhs=rhs)
        pR=fixed_relative_map_terminal(pT,shift=shift,rotation=rotation,translation=translation)
        mR=fixed_relative_map_terminal(mT,shift=shift,rotation=rotation,translation=translation)
        M[:,j]=((pR-mR)/(2*delta)).reshape(-1)
    eigvals,eigvecs=np.linalg.eig(M)
    f0=rhs(x0).reshape(-1)
    neutral=float(np.linalg.norm(M@f0-f0)/max(np.linalg.norm(f0),1e-30))
    return {"backend":bname,"n":N,"dimension":dim,"period_hat":float(period_hat),"dt_hat":float(dt_hat),
            "fd_step_over_D":float(fd_step_over_D),"base_relative_map_residual":base_res,
            "time_tangent_neutral_residual":neutral,"monodromy":M,"eigenvalues":eigvals,"eigenvectors":eigvecs}


def kelvin_cartesian_basis(centerline: np.ndarray, *, state0: np.ndarray, mode_m: int=1) -> np.ndarray:
    """Pre-registered four-state complex Kelvin basis embedded in full Cartesian state."""
    _,n,b=bishop_frame(centerline)
    qs=[kelvin_template(centerline,sector="common",helicity=1,m=mode_m),
        kelvin_template(centerline,sector="differential",helicity=1,m=mode_m),
        kelvin_template(centerline,sector="common",helicity=-1,m=mode_m),
        kelvin_template(centerline,sector="differential",helicity=-1,m=mode_m)]
    cols=[]
    for q in qs:
        # embed complex transverse coordinates by real-linearity.
        z=embed_transverse(q.real,n,b)+1j*embed_transverse(q.imag,n,b)
        cols.append(z.reshape(-1))
    Q=np.column_stack(cols)
    Q,_=np.linalg.qr(Q)
    return Q


def kelvin_restricted_true_monodromy(full: dict[str,Any], centerline: np.ndarray, state0: np.ndarray) -> dict[str,Any]:
    M=np.asarray(full["monodromy"],dtype=float)
    Q=kelvin_cartesian_basis(centerline,state0=state0)
    K=np.conjugate(Q).T@M@Q
    vals,vecs=np.linalg.eig(K)
    phases=np.angle(vals)/(2*math.pi)
    # Pre-registered phase statistic: signed mean of the two eigenphases with largest |phase|.
    order=np.argsort(-np.abs(phases))
    sel=order[:2]
    h=float(((phases[sel[0]]+phases[sel[1]]+0.5)%1.0)-0.5)
    leakage=float(np.linalg.norm((np.eye(M.shape[0])-Q@np.conjugate(Q).T)@M@Q)/max(np.linalg.norm(M@Q),1e-30))
    return {"kelvin_block":K,"kelvin_eigenvalues":vals,"kelvin_eigenphases_turns":phases,
            "selected_indices":[int(x) for x in sel],"true_floquet_phase_turns":h,
            "kelvin_subspace_leakage":leakage}
