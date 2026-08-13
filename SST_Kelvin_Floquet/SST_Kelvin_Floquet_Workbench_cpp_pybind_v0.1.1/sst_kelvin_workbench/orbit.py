"""Relative-periodic-orbit search for the counter-rotating two-filament system.

This module is alpha-blind.  Time is non-dimensionalised with
    tau = Omega_Gamma t,   Omega_Gamma = Gamma_scale/(4*pi*D^2).
The base dynamics is the same regularised two-filament Biot--Savart ODE used by
v0.3.  A relative recurrence is accepted only after quotienting global SE(3)
translation/rotation and a *common* cyclic relabelling of both closed filaments.
No independent channel shift is allowed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any, Callable
import numpy as np

from .backend import load_backend
from .dynamics import pair_rhs
from .geometry import make_counter_channels


def circulation_clock(D: float, gamma_plus: float, gamma_minus: float) -> float:
    gscale = 0.5 * (abs(float(gamma_plus)) + abs(float(gamma_minus)))
    if D <= 0 or gscale <= 0:
        raise ValueError("D and circulation scale must be positive")
    return gscale / (4.0 * math.pi * D * D)


def pair_rhs_hat(state: np.ndarray, *, D: float, gamma_plus: float, gamma_minus: float,
                 eps_over_D: float, backend: Any, remove_tangential_gauge: bool = True) -> np.ndarray:
    """Dimensionless geometric filament RHS in physical X coordinates.

    Since X is kept in physical coordinates, dX/dtau = u/Omega_Gamma.  By default
    the local tangential component is removed independently on each closed filament.
    This is a pure reparametrisation gauge for centerline-shape evolution and prevents
    Lagrangian marker clustering from masquerading as physical non-recurrence.
    """
    x = np.asarray(state, dtype=float)
    if x.ndim != 3 or x.shape[0] != 2 or x.shape[2] != 3:
        raise ValueError("state must have shape (2,N,3)")
    om = circulation_clock(D, gamma_plus, gamma_minus)
    v = np.asarray(pair_rhs(np.ascontiguousarray(x[0]), np.ascontiguousarray(x[1]),
                 gamma_plus, gamma_minus, eps_over_D * D, backend=backend), dtype=float).reshape((2, x.shape[1], 3))
    if remove_tangential_gauge:
        for ch in range(2):
            chord=np.roll(x[ch],-1,axis=0)-np.roll(x[ch],1,axis=0)
            t=chord/np.maximum(np.linalg.norm(chord,axis=1)[:,None],1e-30)
            v[ch]-=np.einsum("ij,ij->i",v[ch],t)[:,None]*t
    return v / om


def rk4_step(state: np.ndarray, dt_hat: float, rhs: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    x = np.asarray(state, dtype=float)
    h = float(dt_hat)
    k1 = rhs(x)
    k2 = rhs(x + 0.5*h*k1)
    k3 = rhs(x + 0.5*h*k2)
    k4 = rhs(x + h*k3)
    return x + (h/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def kabsch_row(moving: np.ndarray, reference: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Return proper row-vector rotation Q and translation t: moving@Q+t ~= reference."""
    x = np.asarray(moving, dtype=float)
    y = np.asarray(reference, dtype=float)
    if x.shape != y.shape or x.ndim != 2 or x.shape[1] != 3:
        raise ValueError("moving/reference must share shape (M,3)")
    xm = x.mean(axis=0); ym = y.mean(axis=0)
    xc = x - xm; yc = y - ym
    H = xc.T @ yc
    U, _, Vt = np.linalg.svd(H)
    Q = U @ Vt
    if np.linalg.det(Q) < 0:
        U[:, -1] *= -1.0
        Q = U @ Vt
    t = ym - xm @ Q
    aligned = x @ Q + t
    rms = float(np.sqrt(np.mean(np.sum((aligned-y)**2, axis=1))))
    return Q, t, rms


def apply_common_shift(state: np.ndarray, shift: int) -> np.ndarray:
    return np.roll(np.asarray(state), -int(shift), axis=1)


def apply_relative_group(state: np.ndarray, *, shift: int, rotation: np.ndarray,
                         translation: np.ndarray) -> np.ndarray:
    s = apply_common_shift(state, shift)
    return s @ np.asarray(rotation, dtype=float) + np.asarray(translation, dtype=float)


def best_relative_alignment(reference: np.ndarray, current: np.ndarray, *, D: float,
                            shifts: list[int] | None = None) -> dict[str, Any]:
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    if ref.shape != cur.shape or ref.ndim != 3 or ref.shape[0] != 2 or ref.shape[2] != 3:
        raise ValueError("reference/current must have shape (2,N,3)")
    N = ref.shape[1]
    if shifts is None:
        shifts = list(range(N))
    ref_flat = ref.reshape((-1,3))
    best = None
    for q in shifts:
        shifted = apply_common_shift(cur, q)
        Q, t, rms = kabsch_row(shifted.reshape((-1,3)), ref_flat)
        aligned = shifted @ Q + t
        ch = np.sqrt(np.mean(np.sum((aligned-ref)**2, axis=2), axis=1))
        rec = {
            "shift": int(q), "rotation": Q, "translation": t,
            "rms": float(rms), "rms_over_D": float(rms/D),
            "plus_rms_over_D": float(ch[0]/D), "minus_rms_over_D": float(ch[1]/D),
            "det_rotation": float(np.linalg.det(Q)),
        }
        if best is None or rec["rms_over_D"] < best["rms_over_D"]:
            best = rec
    assert best is not None
    return best


def segment_quality(state: np.ndarray) -> dict[str, float]:
    x = np.asarray(state, dtype=float)
    vals = []
    for ch in range(2):
        ds = np.linalg.norm(np.roll(x[ch], -1, axis=0)-x[ch], axis=1)
        vals.append(ds)
    ds = np.concatenate(vals)
    return {
        "min_segment": float(ds.min()), "max_segment": float(ds.max()),
        "mean_segment": float(ds.mean()), "max_over_min_segment": float(ds.max()/max(ds.min(),1e-30)),
    }


def pair_min_distance(state: np.ndarray) -> float:
    p,m=np.asarray(state[0]),np.asarray(state[1])
    # Pointwise all-pairs diagnostic only; segment intersection is not inferred.
    d=p[:,None,:]-m[None,:,:]
    return float(np.sqrt(np.min(np.sum(d*d,axis=2))))


@dataclass
class RPOCandidate:
    n: int
    D: float
    offset_over_D: float
    eps_over_D: float
    channel_phase_rad: float
    gamma_plus: float
    gamma_minus: float
    backend: str
    period_hat: float
    dt_hat: float
    step: int
    shift: int
    recurrence_rms_over_D: float
    plus_rms_over_D: float
    minus_rms_over_D: float
    endpoint_vectorfield_error: float
    pair_min_distance_over_D: float
    segment_max_over_min: float
    rotation: list[list[float]]
    translation_over_D: list[float]
    accepted: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def endpoint_vectorfield_compatibility(x0: np.ndarray, xT: np.ndarray, alignment: dict[str,Any],
                                        rhs: Callable[[np.ndarray],np.ndarray]) -> float:
    """For a true RPO, fixed group action should also map f(X_T) to f(X_0)."""
    f0 = rhs(x0)
    fT = rhs(xT)
    fT = apply_common_shift(fT, alignment["shift"]) @ np.asarray(alignment["rotation"])
    num = float(np.linalg.norm(fT-f0))
    den = max(float(np.linalg.norm(f0)), 1e-30)
    return num/den


def search_relative_periodic_orbit(centerline: np.ndarray, *, D: float,
                                   offset_over_D: float = 0.5, eps_over_D: float = 0.05,
                                   channel_phase: float = 0.0,
                                   gamma_plus: float = 1.0, gamma_minus: float = -1.0,
                                   dt_hat: float = 0.01, max_time_hat: float = 8.0,
                                   min_time_hat: float = 0.5, snapshot_stride: int = 5,
                                   recurrence_tol_over_D: float = 0.05,
                                   force_python: bool = False, skip_build: bool = False,
                                   force_build: bool = False, build_verbose: bool = False,
                                   return_trajectory: bool = False) -> dict[str, Any]:
    """Integrate once and find the best relative recurrence along the trajectory."""
    c=np.ascontiguousarray(centerline,dtype=float)
    p,m,_,_=make_counter_channels(c, offset_over_D*D, phase=channel_phase)
    x0=np.stack((p,m),axis=0)
    backend,bname=load_backend(force_python=force_python,skip_build=skip_build,
                               force_build=force_build,build_verbose=build_verbose)
    rhs=lambda x: pair_rhs_hat(x,D=D,gamma_plus=gamma_plus,gamma_minus=gamma_minus,
                               eps_over_D=eps_over_D,backend=backend)
    x=x0.copy()
    nsteps=int(math.ceil(max_time_hat/dt_hat))
    minstep=int(math.ceil(min_time_hat/dt_hat))
    best=None; rows=[]; trajectory=[]; termination_reason="max_time_reached"; termination_time_hat=float(max_time_hat)
    if return_trajectory:
        trajectory.append((0.0,x.copy()))
    for step in range(1,nsteps+1):
        x=rk4_step(x,dt_hat,rhs)
        if not np.all(np.isfinite(x)):
            termination_reason="nonfinite_state"; termination_time_hat=step*dt_hat; break
        if return_trajectory and step%snapshot_stride==0:
            trajectory.append((step*dt_hat,x.copy()))
        if step < minstep or step%snapshot_stride:
            continue
        align=best_relative_alignment(x0,x,D=D)
        q=segment_quality(x); pmin=pair_min_distance(x)/D
        row={"step":step,"time_hat":step*dt_hat,"recurrence_rms_over_D":align["rms_over_D"],
             "shift":align["shift"],"plus_rms_over_D":align["plus_rms_over_D"],
             "minus_rms_over_D":align["minus_rms_over_D"],"pair_min_distance_over_D":pmin,
             "segment_max_over_min":q["max_over_min_segment"]}
        rows.append(row)
        if best is None or align["rms_over_D"] < best["alignment"]["rms_over_D"]:
            best={"step":step,"state":x.copy(),"alignment":align,"quality":q,"pair_min_distance_over_D":pmin}
        if pmin <= eps_over_D:
            termination_reason="cross_channel_core_overlap"; termination_time_hat=step*dt_hat; break
    if best is None:
        raise RuntimeError("trajectory ended before any recurrence snapshot was eligible")
    vferr=endpoint_vectorfield_compatibility(x0,best["state"],best["alignment"],rhs)
    a=best["alignment"]
    accepted=(a["rms_over_D"] < recurrence_tol_over_D and vferr < max(2*recurrence_tol_over_D,0.05)
              and best["quality"]["max_over_min_segment"] < 8.0 and best["pair_min_distance_over_D"] > eps_over_D)
    cand=RPOCandidate(
        n=len(c),D=float(D),offset_over_D=float(offset_over_D),eps_over_D=float(eps_over_D),
        channel_phase_rad=float(channel_phase),gamma_plus=float(gamma_plus),gamma_minus=float(gamma_minus),backend=bname,
        period_hat=float(best["step"]*dt_hat),dt_hat=float(dt_hat),step=int(best["step"]),shift=int(a["shift"]),
        recurrence_rms_over_D=float(a["rms_over_D"]),plus_rms_over_D=float(a["plus_rms_over_D"]),
        minus_rms_over_D=float(a["minus_rms_over_D"]),endpoint_vectorfield_error=float(vferr),
        pair_min_distance_over_D=float(best["pair_min_distance_over_D"]),
        segment_max_over_min=float(best["quality"]["max_over_min_segment"]),
        rotation=np.asarray(a["rotation"]).tolist(),translation_over_D=(np.asarray(a["translation"])/D).tolist(),
        accepted=bool(accepted))
    out={"protocol":"ALPHA_BLIND_RPO_SEARCH","candidate":cand.to_dict(),"recurrence_trace":rows,
         "termination_reason":termination_reason,"termination_time_hat":float(termination_time_hat),
         "initial_state":x0,"terminal_state":best["state"]}
    if return_trajectory:
        out["trajectory"]=trajectory
    return out


def scan_rpo_seeds(centerline: np.ndarray, *, D: float,
                   offsets=(0.30,0.50,0.70), eps_values=(0.05,0.10),
                   phases=(0.0, math.pi/4, math.pi/2),
                   dt_hat: float = 0.02, max_time_hat: float = 6.0,
                   min_time_hat: float = 0.5, snapshot_stride: int = 5,
                   force_python: bool=False, skip_build: bool=False) -> list[dict[str,Any]]:
    rows=[]; first=True
    for off in offsets:
        for eps in eps_values:
            for ph in phases:
                r=search_relative_periodic_orbit(centerline,D=D,offset_over_D=float(off),eps_over_D=float(eps),
                    channel_phase=float(ph),dt_hat=dt_hat,max_time_hat=max_time_hat,min_time_hat=min_time_hat,
                    snapshot_stride=snapshot_stride,force_python=force_python,skip_build=(skip_build or not first))
                first=False
                c=r["candidate"]
                rows.append({k:v for k,v in c.items() if k not in {"rotation","translation_over_D"}})
    return sorted(rows,key=lambda z:z["recurrence_rms_over_D"])
