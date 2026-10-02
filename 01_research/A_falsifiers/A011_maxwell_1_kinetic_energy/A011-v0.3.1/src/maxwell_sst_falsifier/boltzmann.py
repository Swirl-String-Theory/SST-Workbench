from __future__ import annotations

"""Boltzmann-1877 inspired state-counting and equilibrium diagnostics.

The functions in this module deliberately separate:
- a labelled microscopic *complexion* count,
- an occupation/state distribution,
- coarse-grained entropy derived from the multiplicity of that distribution.

No state-counting measure is inferred from geometry alone.  All counts supplied to
these routines must come from a preregistered solver/sampler/experiment.
"""

from collections import defaultdict
import math
from typing import Any, Iterable

import numpy as np

from .constants import EV_J, K_B_J_PER_K
from .io import ffloat


def log_multinomial_complexions(counts: Iterable[float], degeneracies: Iterable[float] | None = None) -> float:
    """Return log P = log(N!/prod w_i!) + sum w_i log g_i.

    `counts` may be integer-valued floats for CSV convenience.  The gamma function
    permits numerically stable evaluation for very large N without constructing N!.
    Degeneracy g_i counts equiprobable labelled sub-states within bin i.
    """
    w = np.asarray(list(counts), dtype=float)
    if np.any(w < 0):
        raise ValueError("occupation counts must be non-negative")
    if np.any(np.abs(w - np.rint(w)) > 1e-9):
        raise ValueError("occupation counts must be integer valued")
    if degeneracies is None:
        g = np.ones_like(w)
    else:
        g = np.asarray(list(degeneracies), dtype=float)
        if len(g) != len(w) or np.any(g <= 0):
            raise ValueError("degeneracies must be positive and match counts")
    n = float(np.sum(w))
    logp = math.lgamma(n + 1.0) - float(np.sum([math.lgamma(x + 1.0) for x in w]))
    logp += float(np.sum(w * np.log(g)))
    return logp


def _r2(y: np.ndarray, yhat: np.ndarray) -> float:
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 if ss_tot <= 1e-300 else 1.0 - ss_res / ss_tot


def permutability_audit(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Compute combinatorial multiplicities for preregistered state distributions.

    Schema: ensemble_id,knot,invariant_sector,position_bin,energy_bin,energy_eV,
    occupation,degeneracy.

    Joint, energy-marginal, and position-marginal multiplicities are reported.
    They are not asserted to be additive entropy components; correlations make the
    three combinatorial counts distinct.
    """
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[(r.get("ensemble_id", ""), r.get("knot", ""), r.get("invariant_sector", ""))].append(r)
    out: list[dict[str, Any]] = []
    for (eid, knot, sector), rr in sorted(groups.items()):
        occ = []
        deg = []
        e_marg: dict[str, float] = defaultdict(float)
        x_marg: dict[str, float] = defaultdict(float)
        for r in rr:
            w = ffloat(r, "occupation")
            if w is None:
                continue
            d = ffloat(r, "degeneracy", 1.0) or 1.0
            occ.append(w); deg.append(d)
            e_marg[r.get("energy_bin", str(r.get("energy_eV", "")))] += w
            x_marg[r.get("position_bin", "")] += w
        if not occ:
            out.append({"ensemble_id": eid, "knot": knot, "invariant_sector": sector, "status": "INDETERMINATE", "reason": "no occupations"})
            continue
        log_joint = log_multinomial_complexions(occ, deg)
        log_e = log_multinomial_complexions(e_marg.values())
        log_x = log_multinomial_complexions(x_marg.values())
        out.append({
            "ensemble_id": eid, "knot": knot, "invariant_sector": sector,
            "N": int(round(sum(occ))), "log_complexions_joint": log_joint,
            "S_perm_joint_J_per_K": K_B_J_PER_K * log_joint,
            "log_complexions_energy_marginal": log_e,
            "log_complexions_position_marginal": log_x,
            "correlation_excess_nats": log_joint - log_e - log_x,
            "status": "COMPUTED",
        })
    return out


def boltzmann_occupation_audit(rows: list[dict[str, str]], temperature_K: float, rel_T_tol: float = 0.10, min_r2: float = 0.98) -> list[dict[str, Any]]:
    """Fit observed state occupations to p_i propto g_i exp(-E_i/kBT).

    Schema: ensemble_id,knot,invariant_sector,state_id,energy_eV,occupation,degeneracy.
    The fit uses ln(occupation/degeneracy) versus energy.  A separate KL divergence
    compares normalized observed occupations with the preregistered temperature.
    """
    if temperature_K <= 0:
        raise ValueError("temperature_K must be positive")
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        groups[(r.get("ensemble_id", ""), r.get("knot", ""), r.get("invariant_sector", ""))].append(r)
    beta_ref_eV = EV_J / (K_B_J_PER_K * temperature_K)
    out: list[dict[str, Any]] = []
    for (eid, knot, sector), rr in sorted(groups.items()):
        E=[]; W=[]; G=[]
        for r in rr:
            e=ffloat(r,"energy_eV"); w=ffloat(r,"occupation"); g=ffloat(r,"degeneracy",1.0) or 1.0
            if e is None or w is None or w <= 0 or g <= 0: continue
            E.append(e); W.append(w); G.append(g)
        if len(E) < 3 or len(set(E)) < 2:
            out.append({"ensemble_id":eid,"knot":knot,"invariant_sector":sector,"status":"INDETERMINATE","reason":"need >=3 positive occupation rows and >=2 energies"}); continue
        e=np.asarray(E,float); w=np.asarray(W,float); g=np.asarray(G,float)
        y=np.log(w/g)
        slope,intercept=np.polyfit(e,y,1); yhat=slope*e+intercept
        fit_r2=_r2(y,yhat)
        T_fit=float("inf") if slope >= 0 else EV_J/((-slope)*K_B_J_PER_K)
        relT=float("inf") if not math.isfinite(T_fit) else abs(T_fit-temperature_K)/temperature_K
        p_obs=w/np.sum(w)
        z=np.sum(g*np.exp(-beta_ref_eV*(e-np.min(e))))
        p_ref=g*np.exp(-beta_ref_eV*(e-np.min(e)))/z
        kl=max(0.0,float(np.sum(p_obs*np.log(np.maximum(p_obs,1e-300)/np.maximum(p_ref,1e-300)))))
        status="PASS" if slope < 0 and relT <= rel_T_tol and fit_r2 >= min_r2 else "FAIL"
        out.append({
            "ensemble_id":eid,"knot":knot,"invariant_sector":sector,"n_states":len(e),
            "slope_per_eV":float(slope),"T_fit_K":T_fit,"T_reference_K":temperature_K,
            "relative_T_error":relT,"r2":fit_r2,"KL_observed_vs_reference_nats":kl,
            "relative_T_tolerance":rel_T_tol,"min_r2":min_r2,"status":status,
        })
    return out


def detailed_balance_audit(rows: list[dict[str, str]], temperature_K: float, log_ratio_tol: float = 0.20) -> list[dict[str, Any]]:
    """Optional microscopic-reversibility guard for an equilibrium claim.

    Uses k_ij/k_ji = (g_j/g_i) exp[-beta(E_j-E_i)].  Transition counts may be
    proportional to rates if exposure times are equal and preregistered as such.
    """
    beta = EV_J/(K_B_J_PER_K*temperature_K)
    out=[]
    for r in rows:
        Ei=ffloat(r,"E_i_eV"); Ej=ffloat(r,"E_j_eV")
        cij=ffloat(r,"count_i_to_j"); cji=ffloat(r,"count_j_to_i")
        gi=ffloat(r,"g_i",1.0) or 1.0; gj=ffloat(r,"g_j",1.0) or 1.0
        if Ei is None or Ej is None or cij is None or cji is None or cij<=0 or cji<=0:
            out.append({"transition_id":r.get("transition_id",""),"status":"INDETERMINATE"}); continue
        log_obs=math.log(cij/cji)
        log_exp=math.log(gj/gi)-beta*(Ej-Ei)
        err=abs(log_obs-log_exp)
        out.append({"transition_id":r.get("transition_id",""),"knot":r.get("knot",""),"log_ratio_observed":log_obs,"log_ratio_expected":log_exp,"abs_log_ratio_error":err,"tolerance":log_ratio_tol,"status":"PASS" if err<=log_ratio_tol else "FAIL"})
    return out


def _log_count(r: dict[str, str]) -> float | None:
    v=ffloat(r,"log_state_count")
    if v is not None: return v
    n=ffloat(r,"state_count")
    if n is None or n<=0: return None
    return math.log(n)


def state_count_entropy_force(rows: list[dict[str, str]], temperature_K: float) -> list[dict[str, Any]]:
    """Compute S=kB ln N and F_ent=T dS/dx along fixed-energy state-count scans.

    Schema: series_id,knot,invariant_sector,x_m,energy_eV,state_count|log_state_count,
    optional T_eff_K.  Derivatives are numerical and require >=3 x points per fixed
    energy.  This does not assume a holographic screen.
    """
    groups: dict[tuple[str,str,str,float], list[dict[str,str]]] = defaultdict(list)
    for r in rows:
        e=ffloat(r,"energy_eV")
        if e is None: continue
        groups[(r.get("series_id",""),r.get("knot",""),r.get("invariant_sector",""),e)].append(r)
    out=[]
    for (sid,knot,sector,e),rr in sorted(groups.items()):
        vals=[]
        for r in rr:
            x=ffloat(r,"x_m"); lc=_log_count(r)
            if x is None or lc is None: continue
            vals.append((x,lc,ffloat(r,"T_eff_K",temperature_K) or temperature_K))
        vals.sort()
        if len(vals)<3:
            for x,lc,T in vals:
                out.append({"series_id":sid,"knot":knot,"invariant_sector":sector,"energy_eV":e,"x_m":x,"log_state_count":lc,"S_J_per_K":K_B_J_PER_K*lc,"T_eff_K":T,"status":"INDETERMINATE","reason":"need >=3 x points at fixed energy"})
            continue
        x=np.asarray([v[0] for v in vals],float); l=np.asarray([v[1] for v in vals],float); T=np.asarray([v[2] for v in vals],float)
        dldx=np.gradient(l,x,edge_order=2)
        for xi,li,Ti,di in zip(x,l,T,dldx):
            dSdx=K_B_J_PER_K*di
            out.append({"series_id":sid,"knot":knot,"invariant_sector":sector,"energy_eV":e,"x_m":float(xi),"log_state_count":float(li),"S_J_per_K":K_B_J_PER_K*float(li),"dSdx_J_per_K_m":float(dSdx),"T_eff_K":float(Ti),"F_entropic_N":float(Ti*dSdx),"status":"COMPUTED"})
    return out


def microcanonical_temperature(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Estimate T from 1/T = dS/dE at fixed position and invariant sector."""
    groups: dict[tuple[str,str,str,float], list[tuple[float,float]]] = defaultdict(list)
    for r in rows:
        x=ffloat(r,"x_m"); e=ffloat(r,"energy_eV"); lc=_log_count(r)
        if x is None or e is None or lc is None: continue
        groups[(r.get("series_id",""),r.get("knot",""),r.get("invariant_sector",""),x)].append((e,lc))
    out=[]
    for (sid,knot,sector,x),vals in sorted(groups.items()):
        vals=sorted(vals)
        if len(vals)<3:
            out.append({"series_id":sid,"knot":knot,"invariant_sector":sector,"x_m":x,"status":"INDETERMINATE","reason":"need >=3 energies"}); continue
        e=np.asarray([a for a,_ in vals],float); l=np.asarray([b for _,b in vals],float)
        slope,intercept=np.polyfit(e,l,1)
        # S=kB lnN and E_J=eV*EV_J => 1/T=(kB/EV_J)*dlnN/dE_eV
        T=float("inf") if slope<=0 else EV_J/(K_B_J_PER_K*slope)
        out.append({"series_id":sid,"knot":knot,"invariant_sector":sector,"x_m":x,"dlogN_dE_per_eV":float(slope),"T_micro_K":T,"r2":_r2(l,slope*e+intercept),"status":"COMPUTED" if math.isfinite(T) else "NONPOSITIVE_DSD_E"})
    return out


def maximum_permutability_audit(
    distribution_rows: list[dict[str, str]],
    permutability_rows: list[dict[str, Any]],
    logP_tol: float = 1e-9,
    energy_rel_tol: float = 1e-9,
) -> list[dict[str, Any]]:
    """Test Boltzmann's maximum-multiplicity equilibrium selection.

    Candidate distributions are grouped by `macrostate_id`.  Every candidate in a
    macrostate must have the same total N and total energy (within tolerance).  One
    candidate must be marked `observed=true`.  Its log multiplicity must equal the
    maximum candidate value within `logP_tol`.
    """
    meta: dict[str, dict[str, Any]] = {}
    for r in distribution_rows:
        eid=r.get("ensemble_id","")
        m=meta.setdefault(eid,{"macrostate_id":r.get("macrostate_id","") or "default","observed":False,"N":0.0,"E_total_eV":0.0})
        m["observed"] = m["observed"] or str(r.get("observed","")).strip().lower() in {"1","true","yes","y","on"}
        w=ffloat(r,"occupation",0.0) or 0.0; e=ffloat(r,"energy_eV",0.0) or 0.0
        m["N"] += w; m["E_total_eV"] += w*e
    lp={r.get("ensemble_id",""):r.get("log_complexions_joint") for r in permutability_rows if r.get("status")=="COMPUTED"}
    groups:dict[str,list[str]]=defaultdict(list)
    for eid,m in meta.items(): groups[m["macrostate_id"]].append(eid)
    out=[]
    for macro,eids in sorted(groups.items()):
        valid=[e for e in eids if e in lp]
        observed=[e for e in valid if meta[e]["observed"]]
        if len(valid)<2 or len(observed)!=1:
            out.append({"macrostate_id":macro,"status":"INDETERMINATE","reason":"need >=2 candidate distributions and exactly one observed=true"}); continue
        Ns=[meta[e]["N"] for e in valid]; Es=[meta[e]["E_total_eV"] for e in valid]
        sameN=max(Ns)-min(Ns) <= 1e-9*max(max(Ns),1.0)
        escale=max(max(abs(x) for x in Es),1e-300)
        sameE=max(Es)-min(Es) <= energy_rel_tol*escale
        if not sameN or not sameE:
            out.append({"macrostate_id":macro,"status":"INDETERMINATE","reason":"candidate distributions do not share the same N and total energy constraints","N_values":Ns,"E_total_eV_values":Es}); continue
        obs=observed[0]; maxlp=max(float(lp[e]) for e in valid); obslp=float(lp[obs]); deficit=maxlp-obslp
        winners=[e for e in valid if maxlp-float(lp[e])<=logP_tol]
        out.append({"macrostate_id":macro,"observed_ensemble_id":obs,"max_log_complexions":maxlp,"observed_log_complexions":obslp,"logP_deficit":deficit,"maximizing_ensembles":winners,"candidate_count":len(valid),"status":"PASS" if deficit<=logP_tol else "FAIL"})
    return out
