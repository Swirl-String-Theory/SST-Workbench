from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any, Sequence

import numpy as np

from . import constants
from .core import PACKAGE_VERSION, backend_biot_savart_with_jacobian


@dataclass(frozen=True)
class HoleBundleParameters:
    core_radius_over_rc: float
    return_radius_over_rc: float
    circulation_ratio: float
    axis_origin_over_rc: tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis_direction: tuple[float, float, float] = (0.0, 0.0, 1.0)
    model: str = "smooth_coaxial_return_periodic"

    def validate(self) -> None:
        if self.core_radius_over_rc <= 0:
            raise ValueError("core radius must be positive")
        if self.return_radius_over_rc <= self.core_radius_over_rc:
            raise ValueError("return radius must exceed core radius")
        if not math.isfinite(self.circulation_ratio):
            raise ValueError("circulation ratio must be finite")
        if self.model != "smooth_coaxial_return_periodic":
            raise ValueError(f"unsupported model: {self.model}")


def _unit(v: Sequence[float]) -> np.ndarray:
    a=np.asarray(v,float); n=float(np.linalg.norm(a))
    if n<=0 or not math.isfinite(n): raise ValueError("axis direction must be finite and nonzero")
    return a/n


def _q_and_dq(r: float, rb: float, rr: float) -> tuple[float,float]:
    # Enclosed-circulation fraction. Near the axis q~2(r/rb)^2,
    # giving a solid-body-like velocity. q and q' are continuous at rb and rr.
    if r <= 0: return 0.0,0.0
    if r < rb:
        t=r/rb; q=2*t*t-t**4; dq=(4*t-4*t**3)/rb; return q,dq
    if r < rr:
        s=(r-rb)/(rr-rb); q=1-3*s*s+2*s**3; dq=(-6*s+6*s*s)/(rr-rb); return q,dq
    return 0.0,0.0


def bundle_beta_and_jacobian(points: np.ndarray, params: HoleBundleParameters) -> tuple[np.ndarray,np.ndarray]:
    params.validate(); p=np.asarray(points,float)
    if p.ndim!=2 or p.shape[1]!=3: raise ValueError("points must have shape (M,3)")
    origin=np.asarray(params.axis_origin_over_rc,float); ez=_unit(params.axis_direction)
    # Construct deterministic perpendicular basis.
    ref=np.array([1.,0.,0.]) if abs(ez[0])<.9 else np.array([0.,1.,0.])
    ex=ref-np.dot(ref,ez)*ez; ex=ex/np.linalg.norm(ex); ey=np.cross(ez,ex)
    out=np.zeros_like(p); jac=np.zeros((len(p),3,3),float)
    rb=float(params.core_radius_over_rc); rr=float(params.return_radius_over_rc); g=float(params.circulation_ratio)*constants.BETA_0
    R=np.column_stack([ex,ey,ez])
    for i,pt in enumerate(p):
        local=R.T@(pt-origin); x,y=local[0],local[1]; r=math.hypot(x,y); q,dq=_q_and_dq(r,rb,rr)
        if r<1e-14:
            A=2*g/(rb*rb); Aprime=0.0
        else:
            A=g*q/(r*r); Aprime=g*(dq/(r*r)-2*q/(r**3))
        b_local=np.array([-A*y,A*x,0.0]); J=np.zeros((3,3),float)
        if r<1e-14:
            J[0,1]=-A; J[1,0]=A
        else:
            xr=x/r; yr=y/r
            J[0,0]=-y*Aprime*xr; J[0,1]=-A-y*Aprime*yr
            J[1,0]= A+x*Aprime*xr; J[1,1]=x*Aprime*yr
        out[i]=R@b_local; jac[i]=R@J@R.T
    return out,jac


def make_combined_clock_evaluator(curve: np.ndarray, *, epsilon: float, bundle: HoleBundleParameters, force_python: bool=False, auto_build: bool=True, minimum_s2: float=1e-14):
    c=np.asarray(curve,float); backend_cache=None
    def evaluate(point: np.ndarray):
        nonlocal backend_cache
        p=np.asarray(point,float).reshape(1,3)
        kb,kj,backend=backend_biot_savart_with_jacobian(c.tolist(),p.tolist(),epsilon=epsilon,force_python=force_python,auto_build=auto_build if backend_cache is None else False)
        if backend_cache is None: backend_cache=backend
        bb,bj=bundle_beta_and_jacobian(p,bundle)
        b=np.asarray(kb,float)[0]+bb[0]; j=np.asarray(kj,float)[0]+bj[0]
        s2=1-float(np.dot(b,b))
        if not math.isfinite(s2) or s2<=minimum_s2:
            from .geodesic import ClockDomainError
            raise ClockDomainError(f"combined clock domain violated: S^2={s2!r}")
        s=math.sqrt(s2); grad=-(j.T@b)/s
        return s,grad,{"backend":backend_cache,"beta":b,"jacobian":j,"S2":s2,"S":s,"grad_S":grad,"bundle":asdict(bundle)}
    return evaluate


def fit_rigid_motion(points: np.ndarray, velocities: np.ndarray) -> dict[str,Any]:
    x=np.asarray(points,float); u=np.asarray(velocities,float); xc=x.mean(axis=0); r=x-xc
    A=np.zeros((3*len(x),6),float); b=u.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        # U + Omega x r
        A[3*i:3*i+3,:3]=np.eye(3)
        A[3*i:3*i+3,3:]=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float)
    coeff,*_=np.linalg.lstsq(A,b,rcond=None); pred=(A@coeff).reshape(-1,3); res=u-pred
    denom=float(np.linalg.norm(u)); rel=float(np.linalg.norm(res)/denom) if denom>0 else 0.0
    return {"translation_beta":coeff[:3].tolist(),"angular_rate_dimensionless":coeff[3:].tolist(),"relative_shape_residual":rel,"residual_norm":float(np.linalg.norm(res)),"velocity_norm":denom}


def evaluate_bundle_shape_residual(curve: np.ndarray, *, epsilon: float, bundle: HoleBundleParameters|None, force_python: bool=False, auto_build: bool=True) -> dict[str,Any]:
    c=np.asarray(curve,float)
    kb,kj,backend=backend_biot_savart_with_jacobian(c.tolist(),c.tolist(),epsilon=epsilon,force_python=force_python,auto_build=auto_build)
    knot=np.asarray(kb,float)
    if bundle is None:
        bg=np.zeros_like(knot); params=None
    else:
        bg,_=bundle_beta_and_jacobian(c,bundle); params=asdict(bundle)
    total=knot+bg; fit=fit_rigid_motion(c,total)
    return {"schema":"sst.fermat.hole-bundle-shape-residual.v0.6.0","package_version":PACKAGE_VERSION,"bundle":params,"backend":backend,"fit":fit,"knot_beta_rms":float(np.sqrt(np.mean(np.sum(knot*knot,axis=1)))),"bundle_beta_rms":float(np.sqrt(np.mean(np.sum(bg*bg,axis=1)))),"total_beta_max":float(np.max(np.linalg.norm(total,axis=1))),"global_closed_orbit_certified":False,"qsm_certified":False}


def estimate_axial_hole_radius(curve: np.ndarray, *, quantile: float=.02) -> float:
    c=np.asarray(curve,float); centered=c-c.mean(axis=0); radial=np.linalg.norm(centered[:,:2],axis=1)
    return float(np.quantile(radial,quantile))


def clock_chain(bundle: HoleBundleParameters, *, effective_area_over_rc2: float|None=None, reference_omega_over_c_per_rc: float=1.0) -> dict[str,Any]:
    bundle.validate(); area=effective_area_over_rc2 if effective_area_over_rc2 is not None else math.pi*bundle.core_radius_over_rc**2
    gamma_dimless=2*math.pi*constants.BETA_0*bundle.circulation_ratio
    mean_vorticity_dimless=gamma_dimless/area
    angular_rate_dimless=.5*mean_vorticity_dimless
    d_tau_dt=angular_rate_dimless/reference_omega_over_c_per_rc
    return {"Gamma_over_c_rc":gamma_dimless,"A_eff_over_rc2":area,"mean_vorticity_over_c_per_rc":mean_vorticity_dimless,"Omega_clock_over_c_per_rc":angular_rate_dimless,"reference_omega_over_c_per_rc":reference_omega_over_c_per_rc,"d_tau_dt":d_tau_dt,"guard":"Omega=zeta/2 is specific to a locally solid-body-like core; tau requires an independently fixed reference frequency."}
