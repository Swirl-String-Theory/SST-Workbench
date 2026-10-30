from __future__ import annotations

"""Conditional Verlinde-style closure diagnostics for SST.

These routines are *tests of optional bridge assumptions*, not SST axioms.  They are
only promoted to closure failures when the corresponding claims are enabled in the
campaign config.
"""

from collections import defaultdict
import math
from typing import Any
import numpy as np

from .constants import C_LIGHT, G_NEWTON, HBAR, K_B_J_PER_K, PLANCK_LENGTH, R_C, RHO_F
from .io import ffloat


def canonical_holographic_scale_check() -> dict[str, float]:
    ratio=(R_C/PLANCK_LENGTH)**2
    G_naive=C_LIGHT**3*R_C**2/HBAR
    return {
        "planck_length_m": PLANCK_LENGTH,
        "r_c_m": R_C,
        "r_c2_over_lP2": ratio,
        "bits_per_r_c2_if_area_law": ratio,
        "G_if_one_bit_per_r_c2_SI": G_naive,
        "G_naive_over_G": G_naive/G_NEWTON,
    }


def entropy_displacement_audit(rows:list[dict[str,str]], rel_tol:float=0.10)->list[dict[str,Any]]:
    out=[]
    for r in rows:
        m=ffloat(r,"probe_mass_kg"); obs=ffloat(r,"dSdx_J_per_K_m")
        if m is None or m<=0 or obs is None:
            out.append({"sample_id":r.get("sample_id",""),"status":"INDETERMINATE"}); continue
        pred=2*math.pi*K_B_J_PER_K*m*C_LIGHT/HBAR
        rel=abs(obs-pred)/max(abs(pred),1e-300)
        out.append({"sample_id":r.get("sample_id",""),"probe_mass_kg":m,"dSdx_observed_J_per_K_m":obs,"dSdx_verlinde_J_per_K_m":pred,"ratio_observed_to_verlinde":obs/pred,"relative_error":rel,"tolerance":rel_tol,"status":"PASS" if rel<=rel_tol else "FAIL"})
    return out


def force_reference_audit(entropy_force:list[dict[str,Any]], refs:list[dict[str,str]], rel_tol:float=0.10)->list[dict[str,Any]]:
    """Compare entropy-gradient force against independent hydrodynamic reference.

    force_reference.csv: series_id,x_m,hyd_force_N OR
    probe_mass_kg,pressure_gradient_Pa_per_m.  In the latter case SST Euler closure
    F_hyd=-(m/rho_f) dp/dx is used.
    """
    refmap={}
    for r in refs:
        sid=r.get("series_id",""); x=ffloat(r,"x_m")
        if x is None: continue
        F=ffloat(r,"hyd_force_N")
        if F is None:
            m=ffloat(r,"probe_mass_kg"); gp=ffloat(r,"pressure_gradient_Pa_per_m")
            if m is not None and gp is not None: F=-(m/RHO_F)*gp
        refmap[(sid,x)]=F
    out=[]
    for e in entropy_force:
        if e.get("status")!="COMPUTED": continue
        key=(e.get("series_id",""),e.get("x_m"))
        Fref=refmap.get(key); Fent=e.get("F_entropic_N")
        if Fref is None or Fent is None: continue
        scale=max(abs(Fref),abs(Fent),1e-300); rel=abs(Fent-Fref)/scale
        sign_ok=(Fref==0 and abs(Fent)<=1e-300) or (Fref*Fent>0)
        out.append({"series_id":key[0],"x_m":key[1],"F_entropic_N":Fent,"F_hyd_N":Fref,"relative_symmetric_error":rel,"sign_match":sign_ok,"tolerance":rel_tol,"status":"PASS" if sign_ok and rel<=rel_tol else "FAIL"})
    return out


def integrability_audit(rows:list[dict[str,str]], sine_tol:float=0.05)->list[dict[str,Any]]:
    """Test grad(1/T) x grad(p)=0 using equivalent grad(T) parallel grad(p).

    Schema contains gradT_{x,y,z}_K_per_m and gradp_{x,y,z}_Pa_per_m.
    For constant T the condition is satisfied identically.
    """
    out=[]
    for r in rows:
        gt=np.asarray([ffloat(r,"gradT_x_K_per_m",0.0),ffloat(r,"gradT_y_K_per_m",0.0),ffloat(r,"gradT_z_K_per_m",0.0)],float)
        gp=np.asarray([ffloat(r,"gradp_x_Pa_per_m",0.0),ffloat(r,"gradp_y_Pa_per_m",0.0),ffloat(r,"gradp_z_Pa_per_m",0.0)],float)
        nt=float(np.linalg.norm(gt)); npg=float(np.linalg.norm(gp))
        if nt<=1e-300 or npg<=1e-300: sine=0.0
        else: sine=float(np.linalg.norm(np.cross(gt,gp))/(nt*npg))
        out.append({"sample_id":r.get("sample_id",""),"cross_sine":sine,"tolerance":sine_tol,"status":"PASS" if sine<=sine_tol else "FAIL"})
    return out


def screen_audit(rows:list[dict[str,str]], area_slope_tol:float=0.05, equipartition_rel_tol:float=0.10, G_rel_tol:float=0.10)->list[dict[str,Any]]:
    groups:dict[str,list[dict[str,str]]]=defaultdict(list)
    for r in rows: groups[r.get("screen_series_id","")].append(r)
    out=[]
    for sid,rr in sorted(groups.items()):
        row_results=[]; Avals=[]; Nvals=[]; gerrs=[]; eqerrs=[]
        for r in rr:
            R=ffloat(r,"radius_m"); A=ffloat(r,"area_m2")
            if A is None and R is not None: A=4*math.pi*R*R
            N=ffloat(r,"bits_N"); E=ffloat(r,"energy_J"); T=ffloat(r,"T_K")
            if A is None or A<=0 or N is None or N<=0:
                continue
            Ginf=A*C_LIGHT**3/(N*HBAR)
            gerr=abs(Ginf-G_NEWTON)/G_NEWTON; gerrs.append(gerr)
            eq=None
            if E is not None and T is not None and T>0:
                eq=2*E/(N*K_B_J_PER_K*T); eqerrs.append(abs(eq-1.0))
            Avals.append(A); Nvals.append(N)
            row_results.append({"radius_m":R,"area_m2":A,"bits_N":N,"G_inferred_SI":Ginf,"G_relative_error":gerr,"equipartition_ratio_2E_over_NkBT":eq})
        slope=None; r2=None
        if len(Avals)>=3 and len(set(Avals))>=2:
            x=np.log(np.asarray(Avals)); y=np.log(np.asarray(Nvals)); slope,intercept=np.polyfit(x,y,1)
            yhat=slope*x+intercept; ssr=float(np.sum((y-yhat)**2)); sst=float(np.sum((y-np.mean(y))**2)); r2=1.0 if sst<=1e-300 else 1-ssr/sst
        checks=[]
        if slope is not None: checks.append(abs(float(slope)-1.0)<=area_slope_tol)
        if gerrs: checks.append(max(gerrs)<=G_rel_tol)
        if eqerrs: checks.append(max(eqerrs)<=equipartition_rel_tol)
        status="INDETERMINATE" if not checks else ("PASS" if all(checks) else "FAIL")
        out.append({"screen_series_id":sid,"n_rows":len(row_results),"area_scaling_slope_dlogN_dlogA":None if slope is None else float(slope),"area_scaling_r2":r2,"max_G_relative_error":max(gerrs) if gerrs else None,"max_equipartition_relative_error":max(eqerrs) if eqerrs else None,"area_slope_tolerance":area_slope_tol,"G_relative_tolerance":G_rel_tol,"equipartition_relative_tolerance":equipartition_rel_tol,"rows":row_results,"status":status})
    return out


def newton_power_law_audit(rows:list[dict[str,str]], slope_tol:float=0.10)->list[dict[str,Any]]:
    """Optional radial force-scaling test using independent measured/hydrodynamic F."""
    groups:dict[str,list[tuple[float,float]]]=defaultdict(list)
    for r in rows:
        R=ffloat(r,"radius_m"); F=ffloat(r,"observed_force_N")
        if R is not None and R>0 and F is not None and F!=0: groups[r.get("series_id","")].append((R,abs(F)))
    out=[]
    for sid,vals in sorted(groups.items()):
        if len(vals)<3:
            out.append({"series_id":sid,"status":"INDETERMINATE","reason":"need >=3 radii"}); continue
        x=np.log([v[0] for v in vals]); y=np.log([v[1] for v in vals]); slope,intercept=np.polyfit(x,y,1)
        yhat=slope*x+intercept; ssr=float(np.sum((y-yhat)**2)); sst=float(np.sum((y-np.mean(y))**2)); r2=1.0 if sst<=1e-300 else 1-ssr/sst
        out.append({"series_id":sid,"force_power_slope":float(slope),"expected_slope":-2.0,"abs_slope_error":abs(float(slope)+2.0),"tolerance":slope_tol,"r2":r2,"status":"PASS" if abs(float(slope)+2.0)<=slope_tol else "FAIL"})
    return out


def potential_entropy_audit(rows:list[dict[str,str]], rel_tol:float=0.10)->list[dict[str,Any]]:
    """Audit Verlinde Eq. 3.16: DeltaS/n = -kB DeltaPhi/(2 c^2)."""
    out=[]
    for r in rows:
        ds=ffloat(r,"deltaS_per_bit_J_per_K"); dphi=ffloat(r,"deltaPhi_m2_s2")
        if ds is None or dphi is None:
            out.append({"sample_id":r.get("sample_id",""),"status":"INDETERMINATE"}); continue
        pred=-K_B_J_PER_K*dphi/(2*C_LIGHT**2); rel=abs(ds-pred)/max(abs(pred),1e-300)
        out.append({"sample_id":r.get("sample_id",""),"observed_deltaS_per_bit_J_per_K":ds,"predicted_deltaS_per_bit_J_per_K":pred,"relative_error":rel,"tolerance":rel_tol,"status":"PASS" if rel<=rel_tol else "FAIL"})
    return out
