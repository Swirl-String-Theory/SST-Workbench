from __future__ import annotations
import copy, math
import numpy as np
from ..geometry import ring, symmetric_ring_mode
from ..simulation import PhysicalScale
from .. import native
from ..metrics import linear_fit

GATE="E5"

def _state(ampl: float, phase: float, n: int, scale: PhysicalScale, mode: int) -> dict:
    p=ring(n,1.0) if ampl==0 else symmetric_ring_mode(n,1.0,ampl,mode,phase)
    E=native.filament_energy(p,scale.core_dimless,1.0,1.0)*scale.energy_J
    I=native.impulse(p,1.0,1.0)*scale.impulse_kg_m_s
    vdim=native.biot_savart_velocity(p,scale.core_dimless,1.0,(0,0,0))
    U=np.mean(vdim,axis=0)*scale.velocity_m_s
    Iz=float(I[2]); Uz=float(U[2])
    M=float(Iz/Uz) if abs(Uz)>1e-300 else float("nan")
    return {"amplitude_over_R":ampl,"phase":phase,"energy_J":float(E),"impulse_z_kg_m_s":Iz,"translation_Uz_m_s":Uz,"M_impulse_over_U_kg":M}

def _evaluate_at_n(n:int, gc:dict, scale:PhysicalScale, mode:int)->dict:
    phases=[float(x) for x in gc.get("phases",[0.0])]
    base_states=[_state(0.0,ph,n,scale,mode) for ph in phases]
    E0=float(np.mean([x["energy_J"] for x in base_states])); M0=float(np.mean([x["M_impulse_over_U_kg"] for x in base_states]))
    rows=[]
    for a in [float(x) for x in gc["amplitudes"]]:
        ss=[_state(a,ph,n,scale,mode) for ph in phases]
        E=float(np.mean([x["energy_J"] for x in ss])); M=float(np.mean([x["M_impulse_over_U_kg"] for x in ss]))
        dE=E-E0; dM=M-M0; ratio=dE/dM if np.isfinite(dM) and abs(dM)>0 else float("nan")
        ceff=math.sqrt(ratio) if np.isfinite(ratio) and ratio>0 else float("nan")
        rows.append({"amplitude_over_R":a,"deltaE_J":dE,"deltaM_kg":dM,"C2_blind_m2_s2":ratio,"C_blind_m_s":ceff,"phase_states":ss})
    th=gc["thresholds"]
    valid=[r for r in rows if np.isfinite(r["C2_blind_m2_s2"]) and r["C2_blind_m2_s2"]>0 and abs(r["deltaM_kg"])/max(abs(M0),1e-300)>=th["deltaM_rel_min"]]
    fit=None
    if len(valid)>=2:
        dM=np.array([r["deltaM_kg"] for r in valid]); dE=np.array([r["deltaE_J"] for r in valid]); C=np.array([r["C_blind_m_s"] for r in valid])
        lf=linear_fit(dM,dE); erange=max(float(np.ptp(dE)),1e-300); intercept_rel=abs(lf["intercept"])/erange
        cv=float(np.std(C,ddof=1)/abs(np.mean(C))) if len(C)>1 and np.mean(C)!=0 else float("inf")
        fit={"deltaE_vs_deltaM_slope_m2_s2":lf["slope"],"intercept_J":lf["intercept"],"r2":lf["r2"],"intercept_over_energy_range":intercept_rel,"C_cv":cv,"C_mean_m_s":float(np.mean(C))}
    return {"n_points":n,"base":{"energy_J":E0,"M_kg":M0},"cases":rows,"valid_count":len(valid),"fit":fit}

def run(cfg: dict, scale: PhysicalScale, outdir, rng=None, external_curves=None) -> dict:
    gc=cfg["gates"]["E5"]; mode=int(gc.get("mode",2)); n=int(cfg["simulation"]["n_points"]); th=gc["thresholds"]
    main=_evaluate_at_n(n,gc,scale,mode)
    if main["valid_count"]<th["min_valid_amplitudes"] or main["fit"] is None:
        return {"gate":GATE,"verdict":"INCONCLUSIVE","reason":"Operational inertia change is unresolved or has non-positive DeltaE/DeltaM.","main":main,"thresholds":th,
                "scope_note":"This tests an impulse/translation inertial proxy for a symmetric ±m internal excitation; the closed-filament solver does not model radiative topology change."}
    n_coarse=max(24,n-int(gc.get("resolution_delta_n",12)))
    coarse=_evaluate_at_n(n_coarse,gc,scale,mode)
    cres=float("inf")
    if coarse.get("fit") and np.isfinite(coarse["fit"].get("C_mean_m_s",np.nan)):
        a=main["fit"]["C_mean_m_s"]; b=coarse["fit"]["C_mean_m_s"]
        cres=abs(a-b)/max(abs(a),abs(b),1e-300)
    fit=main["fit"]
    passed=(fit["r2"]>=th["linear_r2_min"] and fit["intercept_over_energy_range"]<=th["intercept_energy_range_max"] and fit["C_cv"]<=th["C_cv_max"] and cres<=th["resolution_C_rel_max"])
    return {"gate":GATE,"hypothesis":"For symmetric zero-first-order-impulse internal excitation, energy change is proportional to an independently measured impulse/translation inertial proxy.",
            "verdict":"PASS" if passed else "FAIL","main":main,"coarse_resolution":coarse,"resolution_C_relative_change":cres,
            "thresholds":th,"blind_note":"The derived speed C is not compared to c, v_swirl, or any other target speed.",
            "scope_note":"This is an operational closure test, not a simulation of photon emission or reconnection.",
            "falsification_meaning":"FAIL rejects a single resolution-stable proportional DeltaE/DeltaM closure for this inertial proxy and excitation family."}
