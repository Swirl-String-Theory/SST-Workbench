"""Alpha-blind Newton--Krylov multiple-shooting RPO solver (v0.5).

The nonlinear target is a relative periodic orbit of the geometric filament flow,
not an alpha fit.  Tangential motion is removed as a centerline reparametrisation
gauge by :func:`pair_rhs_hat`.

A pure longitudinal relabelling of one closed filament is *not* treated as a new
physical parameter.  `fractional_channel_relabel` exists only to verify that this
operation converges to a gauge transformation with resolution.

The shooting correction space is a pre-registered, low-dimensional transverse
Fourier/Kelvin space.  Newton steps are obtained matrix-free with restarted GMRES.
Acceptance is never based on the projected shooting residual alone: a candidate
must subsequently close in the full Cartesian state under one fixed SE(3)+common
cyclic group action.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any, Callable
import numpy as np

from .backend import load_backend
from .geometry import bishop_frame
from .orbit import (pair_rhs_hat, rk4_step, best_relative_alignment,
                    endpoint_vectorfield_compatibility, pair_min_distance,
                    segment_quality, apply_relative_group)


def fractional_closed_shift(points: np.ndarray, shift_turns: float) -> np.ndarray:
    """Periodic fractional relabelling of a closed polygon by linear interpolation.

    `shift_turns=1` is exactly one complete circuit and therefore the identity.
    In the continuum a non-integer shift is also only a reparametrisation of the
    same curve; finite-N interpolation changes the polygon slightly, so this is a
    useful convergence diagnostic rather than a physical deformation coordinate.
    """
    p=np.asarray(points,dtype=float)
    if p.ndim!=2 or p.shape[1]!=3: raise ValueError("points must be (N,3)")
    N=len(p); u=(np.arange(N,dtype=float)+float(shift_turns)*N)%N
    i0=np.floor(u).astype(int); a=u-i0; i1=(i0+1)%N
    return np.ascontiguousarray((1.0-a)[:,None]*p[i0]+a[:,None]*p[i1])


def fractional_channel_relabel(state: np.ndarray, shift_turns: float, channel: int=1) -> np.ndarray:
    x=np.asarray(state,dtype=float).copy()
    if x.ndim!=3 or x.shape[0]!=2 or x.shape[2]!=3: raise ValueError("state must be (2,N,3)")
    x[int(channel)]=fractional_closed_shift(x[int(channel)],shift_turns)
    return x


def _arc_phase(centerline: np.ndarray, m: int) -> np.ndarray:
    c=np.asarray(centerline,dtype=float)
    seg=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)
    s=np.concatenate(([0.0],np.cumsum(seg[:-1])))
    return 2.0*math.pi*int(m)*s/max(float(np.sum(seg)),1e-30)


def transverse_shape_basis(centerline: np.ndarray, *, modes=(1,2), max_cols: int=8) -> np.ndarray:
    """Deterministic real transverse correction basis in full two-channel space.

    For each mode we add common/differential cosine/sine perturbations in the
    Bishop normal/binormal plane.  QR orthonormalisation removes accidental
    dependencies.  Columns are dimensionless unit vectors in flattened Cartesian
    coordinates; physical corrections are `D * B @ a`.
    """
    c=np.asarray(centerline,dtype=float); N=len(c)
    _,n,b=bishop_frame(c)
    cols=[]
    for m in modes:
        ph=_arc_phase(c,m); co=np.cos(ph); si=np.sin(ph)
        # Circular real/imag pair, then common/differential channel parity.
        d0=co[:,None]*n + si[:,None]*b
        d1=-si[:,None]*n + co[:,None]*b
        for parity in (1.0,-1.0):
            for d in (d0,d1):
                arr=np.empty((2,N,3),dtype=float); arr[0]=d; arr[1]=parity*d
                cols.append(arr.reshape(-1))
    A=np.column_stack(cols)
    Q,_=np.linalg.qr(A)
    return np.ascontiguousarray(Q[:,:min(int(max_cols),Q.shape[1])])


def integrate_hat(state0: np.ndarray, *, duration_hat: float, dt_hat: float, rhs: Callable[[np.ndarray],np.ndarray]) -> np.ndarray:
    n=max(1,int(math.ceil(float(duration_hat)/float(dt_hat))))
    h=float(duration_hat)/n; x=np.asarray(state0,dtype=float).copy()
    for _ in range(n): x=rk4_step(x,h,rhs)
    return x


def seed_multiple_shooting_nodes(state0: np.ndarray, *, period_hat: float, segments: int,
                                 dt_hat: float, rhs: Callable[[np.ndarray],np.ndarray]) -> list[np.ndarray]:
    nodes=[np.asarray(state0,dtype=float).copy()]
    dtseg=float(period_hat)/int(segments)
    x=nodes[0]
    for _ in range(1,int(segments)):
        x=integrate_hat(x,duration_hat=dtseg,dt_hat=dt_hat,rhs=rhs)
        nodes.append(x.copy())
    return nodes


def _apply_coeff(node: np.ndarray, basis: np.ndarray, coeff: np.ndarray, D: float) -> np.ndarray:
    return np.asarray(node,dtype=float) + (float(D)*(basis@np.asarray(coeff,dtype=float))).reshape(node.shape)


def _local_basis_from_state(state: np.ndarray, max_cols: int) -> np.ndarray:
    # Midline is used only to orient a correction basis, never as a dynamical model.
    mid=0.5*(np.asarray(state[0])+np.asarray(state[1]))
    return transverse_shape_basis(mid,modes=(1,2,3),max_cols=max_cols)


def multiple_shooting_residual(z: np.ndarray, *, seed_nodes: list[np.ndarray], bases: list[np.ndarray], D: float,
                               base_period_hat: float, dt_hat: float, rhs: Callable[[np.ndarray],np.ndarray],
                               period_scale_limit: float=0.6) -> tuple[np.ndarray, dict[str,Any]]:
    """Square reduced multiple-shooting residual.

    z = [a_0,...,a_{M-1}, eta], where T=T0*exp(clipped eta).  Segment defects are
    projected onto the next node's transverse basis.  Final closure is quotiented
    by the best SE(3)+common cyclic action.  One phase condition anchors a_0 to
    the seed and removes the time-shift null direction.
    """
    M=len(seed_nodes); K=bases[0].shape[1]
    z=np.asarray(z,dtype=float)
    if z.size!=M*K+1: raise ValueError("unexpected shooting vector size")
    aa=z[:M*K].reshape(M,K); eta=float(np.clip(z[-1],-period_scale_limit,period_scale_limit))
    T=float(base_period_hat)*math.exp(eta); dtseg=T/M
    nodes=[_apply_coeff(seed_nodes[j],bases[j],aa[j],D) for j in range(M)]
    pieces=[]; defects=[]; final_align=None
    for j in range(M):
        end=integrate_hat(nodes[j],duration_hat=dtseg,dt_hat=dt_hat,rhs=rhs)
        if j<M-1:
            delta=end-nodes[j+1]
            proj=(bases[j+1].T@delta.reshape(-1))/D
            defects.append(float(np.linalg.norm(delta)/max(np.linalg.norm(nodes[j+1]-nodes[j+1].mean(axis=(0,1))),1e-30)))
        else:
            final_align=best_relative_alignment(nodes[0],end,D=D)
            aligned=apply_relative_group(end,shift=final_align["shift"],rotation=final_align["rotation"],translation=final_align["translation"])
            delta=aligned-nodes[0]
            proj=(bases[0].T@delta.reshape(-1))/D
            defects.append(float(final_align["rms_over_D"]))
        pieces.append(proj)
    # Phase condition: pin the first coefficient. This is deliberately simple,
    # deterministic, alpha-independent, and prevents drift along an arbitrary node phase.
    phase=np.array([aa[0,0]],dtype=float)
    F=np.concatenate(pieces+[phase])
    return F,{"period_hat":T,"eta":eta,"projected_residual_norm":float(np.linalg.norm(F)),
              "segment_full_defects":defects,"max_segment_full_defect":float(max(defects)),
              "final_alignment":final_align}


def gmres_matrix_free(matvec: Callable[[np.ndarray],np.ndarray], b: np.ndarray, *, restart: int=18,
                      tol: float=1e-5) -> tuple[np.ndarray,dict[str,Any]]:
    """Small restarted-GMRES implementation for a matrix-free Newton step."""
    b=np.asarray(b,dtype=float); n=b.size; x=np.zeros(n,dtype=float)
    r=b-matvec(x); beta=float(np.linalg.norm(r))
    if beta<=tol: return x,{"iterations":0,"relative_residual":0.0}
    bnorm=max(float(np.linalg.norm(b)),1e-30); total=0
    for _outer in range(max(1,math.ceil(n/max(1,restart)))):
        r=b-matvec(x); beta=float(np.linalg.norm(r))
        if beta/bnorm<tol: break
        m=min(int(restart),n)
        V=np.zeros((n,m+1)); H=np.zeros((m+1,m)); V[:,0]=r/beta
        g=np.zeros(m+1); g[0]=beta
        xbest=x.copy(); rel=beta/bnorm
        for j in range(m):
            w=matvec(V[:,j]); total+=1
            for i in range(j+1):
                H[i,j]=np.dot(V[:,i],w); w-=H[i,j]*V[:,i]
            H[j+1,j]=np.linalg.norm(w)
            if H[j+1,j]>1e-14: V[:,j+1]=w/H[j+1,j]
            y,*_=np.linalg.lstsq(H[:j+2,:j+1],g[:j+2],rcond=None)
            cand=x+V[:,:j+1]@y
            rr=b-matvec(cand); total+=1; rel=float(np.linalg.norm(rr)/bnorm)
            xbest=cand
            if rel<tol: return xbest,{"iterations":total,"relative_residual":rel}
        x=xbest
    rr=b-matvec(x)
    return x,{"iterations":total,"relative_residual":float(np.linalg.norm(rr)/bnorm)}


@dataclass
class NewtonKrylovResult:
    accepted: bool
    initial_projected_residual: float
    final_projected_residual: float
    residual_reduction_factor: float
    iterations: int
    period_hat: float
    recurrence_rms_over_D: float
    endpoint_vectorfield_error: float
    pair_min_distance_over_D: float
    segment_max_over_min: float
    initial_max_shooting_defect: float
    max_shooting_defect: float
    full_defect_reduction_factor: float
    gmres_last_relative_residual: float
    shift: int
    rotation: list[list[float]]
    translation_over_D: list[float]
    solver_history: list[dict[str,Any]]

    def to_dict(self): return asdict(self)


def newton_krylov_multiple_shooting(centerline: np.ndarray, *, D: float, state0: np.ndarray,
                                     seed_period_hat: float, eps_over_D: float,
                                     gamma_plus: float=1.0,gamma_minus: float=-1.0,
                                     segments: int=3,basis_cols: int=6,dt_hat: float=.01,
                                     max_newton: int=5,newton_fd: float=2e-4,
                                     recurrence_tol_over_D: float=.05,
                                     vf_tol: float=.10,force_python: bool=False,
                                     skip_build: bool=False) -> dict[str,Any]:
    backend,bname=load_backend(force_python=force_python,skip_build=skip_build)
    rhs=lambda x: pair_rhs_hat(x,D=D,gamma_plus=gamma_plus,gamma_minus=gamma_minus,
                               eps_over_D=eps_over_D,backend=backend)
    seed_nodes=seed_multiple_shooting_nodes(state0,period_hat=seed_period_hat,segments=segments,dt_hat=dt_hat,rhs=rhs)
    bases=[_local_basis_from_state(s,basis_cols) for s in seed_nodes]
    K=bases[0].shape[1]; z=np.zeros(segments*K+1,dtype=float)
    F,meta=multiple_shooting_residual(z,seed_nodes=seed_nodes,bases=bases,D=D,base_period_hat=seed_period_hat,dt_hat=dt_hat,rhs=rhs)
    initial=float(np.linalg.norm(F)); initial_full=float(meta["max_segment_full_defect"]); history=[]; gm={"relative_residual":float("nan")}; merit_weight=0.08
    for it in range(int(max_newton)):
        f0=F.copy(); norm0=float(np.linalg.norm(f0))
        def jv(v):
            v=np.asarray(v,dtype=float); nv=max(float(np.linalg.norm(v)),1e-30)
            h=float(newton_fd)/nv
            fp,_=multiple_shooting_residual(z+h*v,seed_nodes=seed_nodes,bases=bases,D=D,base_period_hat=seed_period_hat,dt_hat=dt_hat,rhs=rhs)
            return (fp-f0)/h
        dz,gm=gmres_matrix_free(jv,-f0,restart=min(12,len(z)),tol=2e-3)
        ndz=float(np.linalg.norm(dz));
        if ndz>0.35: dz*=0.35/ndz
        merit0=norm0+merit_weight*float(meta["max_segment_full_defect"])
        accepted_step=False; best=(merit0,z,F,meta,0.0)
        for ls in range(7):
            lam=0.5**ls; zt=z+lam*dz
            # bound shape corrections and period log-scale
            zt[:-1]=np.clip(zt[:-1],-.30,.30); zt[-1]=np.clip(zt[-1],-.45,.45)
            ft,mt=multiple_shooting_residual(zt,seed_nodes=seed_nodes,bases=bases,D=D,base_period_hat=seed_period_hat,dt_hat=dt_hat,rhs=rhs)
            nt=float(np.linalg.norm(ft)); merit=nt+merit_weight*float(mt["max_segment_full_defect"])
            if merit<best[0]: best=(merit,zt,ft,mt,lam)
            if merit < merit0*(1.0-1e-3): accepted_step=True; break
        _,z,F,meta,lam=best
        history.append({"iteration":it,"projected_residual":float(np.linalg.norm(F)),"step_norm":float(np.linalg.norm(dz)),
                        "line_search_lambda":float(lam),"gmres_relative_residual":float(gm["relative_residual"]),
                        "period_hat":float(meta["period_hat"]),"max_segment_full_defect":float(meta["max_segment_full_defect"]),
                        "merit":float(np.linalg.norm(F)+merit_weight*meta["max_segment_full_defect"])})
        if not accepted_step or float(np.linalg.norm(F))<1e-4: break
    aa=z[:segments*K].reshape(segments,K)
    x0corr=_apply_coeff(seed_nodes[0],bases[0],aa[0],D)
    T=float(meta["period_hat"])
    xT=integrate_hat(x0corr,duration_hat=T,dt_hat=dt_hat,rhs=rhs)
    align=best_relative_alignment(x0corr,xT,D=D)
    vf=endpoint_vectorfield_compatibility(x0corr,xT,align,rhs)
    pmin=pair_min_distance(xT)/D; q=segment_quality(xT)
    final=float(np.linalg.norm(F)); accepted=bool(align["rms_over_D"]<recurrence_tol_over_D and vf<vf_tol and
        pmin>eps_over_D and q["max_over_min_segment"]<8.0 and meta["max_segment_full_defect"]<max(.15,3*recurrence_tol_over_D))
    res=NewtonKrylovResult(accepted=accepted,initial_projected_residual=initial,final_projected_residual=final,
        residual_reduction_factor=float(initial/max(final,1e-30)),iterations=len(history),period_hat=T,
        recurrence_rms_over_D=float(align["rms_over_D"]),endpoint_vectorfield_error=float(vf),
        pair_min_distance_over_D=float(pmin),segment_max_over_min=float(q["max_over_min_segment"]),
        initial_max_shooting_defect=initial_full,max_shooting_defect=float(meta["max_segment_full_defect"]),
        full_defect_reduction_factor=float(initial_full/max(float(meta["max_segment_full_defect"]),1e-30)),
        gmres_last_relative_residual=float(gm["relative_residual"]),
        shift=int(align["shift"]),rotation=np.asarray(align["rotation"]).tolist(),translation_over_D=(np.asarray(align["translation"])/D).tolist(),
        solver_history=history)
    return {"backend":bname,"result":res.to_dict(),"corrected_initial_state":x0corr,"terminal_state":xT,"shooting_vector":z,
            "basis_cols":K,"segments":segments}
