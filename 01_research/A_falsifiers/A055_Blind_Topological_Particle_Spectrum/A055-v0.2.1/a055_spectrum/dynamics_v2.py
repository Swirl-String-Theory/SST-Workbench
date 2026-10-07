from __future__ import annotations
import math, json
from pathlib import Path
import numpy as np
from .workbench import find_e011_seedset, find_c006_version
from .providers import select_provider_anchors, resolve_knot_provider
from .c006_bridge import import_c006, provenance as c006_provenance
from .tracking import track_from_finest, select_fine_anchored_branch

def _complex_rows(vals):
    return [{"re":float(complex(z).real),"im":float(complex(z).imag)} for z in vals]
def _complex_matrix(mat):
    a=np.asarray(mat,complex)
    return [[{"re":float(a[i,j].real),"im":float(a[i,j].imag)} for j in range(a.shape[1])] for i in range(a.shape[0])]
def _from_rows(rows): return np.asarray([complex(z["re"],z["im"]) for z in rows],complex)
def _from_matrix(rows): return np.asarray([[complex(z["re"],z["im"]) for z in row] for row in rows],complex)
def _rel_shift(a,b): return abs(a-b)/max(abs(a),abs(b),1e-30)
def _rel_span(xs):
    a=np.asarray(list(xs),float)
    if len(a)<2:return math.inf
    return float((a.max()-a.min())/max(np.median(np.abs(a)),1e-30))

def inspect_static(workbench,topology_id,provider_groups):
    try:
        seed=find_e011_seedset(workbench,topology_id)
        obj=json.loads(seed.read_text(encoding="utf-8")); s=obj.get("summary",{})
        anchors=[a for a in obj.get("provider_anchors",[]) if a.get("static_ready",False)]
        rows=[]
        for a in anchors:
            fm=a.get("finest_metrics",{})
            rows.append({"provider_group":a.get("provider_group"),"carrier_id":a.get("carrier_id"),
                         "Rop":fm.get("Rop"),"Wr":fm.get("Wr"),"reach":fm.get("reach"),
                         "source_locator":a.get("source_locator")})
        available=[r.get("provider_group") for r in rows]
        missing=[pg for pg in provider_groups if pg not in available]
        if len(available)==len(tuple(provider_groups)):
            coverage="FULL_PROVIDER_SET"
        elif len(available)==1:
            coverage="SINGLE_PROVIDER_ONLY"
        elif len(available)==0:
            coverage="NO_PREREGISTERED_PROVIDER"
        else:
            coverage="PARTIAL_PROVIDER_SET"
        return {"status":"STATIC_READY" if s.get("static_ready") else "NOT_STATIC_READY",
                "provider_coverage_status":coverage,
                "available_provider_groups":available,"missing_provider_groups":missing,
                "seedset_path":str(seed),"summary":s,"static_anchors":rows}
    except Exception as e:
        return {"status":"E011_UNAVAILABLE","error":repr(e),"static_anchors":[]}

def run_knot_dynamic(workbench,topology_id,cfg,force_python=False):
    out={"topology_id":topology_id,"kind":"knot"}
    seed=find_e011_seedset(workbench,topology_id)
    anchors,summary,coverage=select_provider_anchors(seed,tuple(cfg["e011_provider_groups"]),topology_id,True)
    if not anchors:
        out.update({"e011_summary":summary,"provider_coverage":coverage,"providers":[],
                    "agreed_modes":[],"dimensionless_dynamic_qualified":False,
                    "true_floquet":[],"true_floquet_qualified":False,
                    "particle_promotion_qualified":False})
        return out
    providers=[resolve_knot_provider(a,workbench,int(cfg["canonical_writhe_sign"])) for a in anchors]
    croot=find_c006_version(workbench); c006=import_c006(croot)
    out["e011_summary"]=summary
    out["provider_coverage"]=coverage
    out["c006_provenance"]=c006_provenance(croot)
    pcfg=cfg["dynamic_presets"][cfg["active_dynamic_preset"]]
    nlad=[int(x) for x in pcfg["n_ladder"]]; mmax=int(pcfg["mode_m_max"])
    reltol=float(pcfg["stable_root_relative_shift_max"]); trcfg=cfg["eigenvector_tracking"]
    rpo_rows=[]; provider_reports=[]
    for p in providers:
        a=p["anchor"]; pg=a.get("provider_group")
        # RPO with same generator parameters; no parameter scan.
        c,norm=p["sample"](int(pcfg["rpo_resolution"]))
        rr=c006["orbit"].search_relative_periodic_orbit(
            c,D=1.0,offset_over_D=float(cfg["offset_over_D"]),eps_over_D=float(cfg["eps_over_D"]),
            channel_phase=float(cfg["channel_phase_rad"]),gamma_plus=float(cfg["gamma_plus_hat"]),
            gamma_minus=float(cfg["gamma_minus_hat"]),dt_hat=float(pcfg["rpo_dt_hat"]),
            max_time_hat=float(pcfg["rpo_max_time_hat"]),min_time_hat=float(cfg["rpo_conditioning"]["min_time_hat"]),
            snapshot_stride=int(cfg["rpo_conditioning"]["snapshot_stride"]),
            recurrence_tol_over_D=float(cfg["rpo_conditioning"]["recurrence_tol_over_D"]),
            force_python=bool(force_python),skip_build=True,return_trajectory=False)
        cand=dict(rr["candidate"])
        rpo_rows.append({"provider_group":pg,"normalization":norm,"candidate":cand,
                         "termination_reason":rr.get("termination_reason")})
        levels={m:[] for m in range(1,mmax+1)}
        for N in nlad:
            cen,nm=p["sample"](N); L=float(nm["normalized_polygon_length"])
            for m in range(1,mmax+1):
                z=c006["dynamics"].projected_kelvin_analysis(
                    cen,D=1.0,offset_over_D=float(cfg["offset_over_D"]),eps_over_D=float(cfg["eps_over_D"]),
                    fd_step_over_D=float(cfg["fd_step_over_D"]),gamma_plus=float(cfg["gamma_plus_hat"]),
                    gamma_minus=float(cfg["gamma_minus_hat"]),channel_phase=float(cfg["channel_phase_rad"]),
                    basis_phase=float(cfg["basis_phase_rad"]),mode_m=m,force_python=bool(force_python),skip_build=True)
                levels[m].append({"N":N,"kD":float(2*math.pi*m/L),"selected_positive_index":int(z["selected_positive_index"]),
                    "eigenvalues":_complex_rows(z["eigenvalues"]),"eigenvectors":_complex_matrix(z["eigenvectors"]),
                    "relative_equilibrium_residual":float(z["rigid"]["relative_equilibrium_residual"]),
                    "backend":str(z["backend"])})
        q=[]
        mode_reports=[]
        for m,rows in levels.items():
            lev=[{"label":r["N"],"eigenvalues":_from_rows(r["eigenvalues"]),"eigenvectors":_from_matrix(r["eigenvectors"])} for r in rows]
            tr=track_from_finest(lev,reltol,float(trcfg["minimum_adjacent_overlap"]),
                                 float(trcfg["eigenvalue_weight"]),float(trcfg["overlap_weight"]))
            fine=rows[-1]; b=select_fine_anchored_branch(tr,fine["selected_positive_index"])
            lam=[complex(x["lambda"]) for x in b["points"]]
            om=[float(z.imag) for z in lam]
            shifts=[_rel_shift(om[i],om[i+1]) for i in range(len(om)-1)]
            qualities=[abs(z.real)/max(abs(z.imag),1e-30) for z in lam]
            ok=bool(b.get("persistent") and all(s<=reltol for s in shifts)
                    and all(qv<=float(trcfg["maximum_re_over_im"]) for qv in qualities))
            rec={"mode_m":m,"qualified":ok,"omega_hat":float(lam[-1].imag),"kD":float(fine["kD"]),
                 "growth_hat":float(lam[-1].real),"min_overlap":float(b.get("min_eigenvector_overlap",0)),
                 "max_shift":float(b.get("max_eigenvalue_shift",math.inf)),
                 "quality_re_over_im":float(qualities[-1]),"levels":rows}
            mode_reports.append(rec)
            if ok:q.append({k:rec[k] for k in ["mode_m","omega_hat","kD","growth_hat","quality_re_over_im","min_overlap","max_shift"]})
        provider_reports.append({"provider_group":pg,"carrier_id":a.get("carrier_id"),"source_sha256":p["source_sha256"],
                                 "representation":p["representation"],"qualified_modes":q,"mode_reports":mode_reports,
                                 "rpo_accepted":bool(cand.get("accepted",False))})
    # Cross-provider mode agreement. Single-provider dynamics are retained diagnostically
    # but can never satisfy the particle-promotion gate.
    bypg={r["provider_group"]:r for r in provider_reports}
    common=None
    for r in provider_reports:
        ms={x["mode_m"] for x in r["qualified_modes"]}
        common=ms if common is None else common & ms
    common=sorted(common or [])
    agreed=[]
    for m in common:
        xs=[next(x for x in r["qualified_modes"] if x["mode_m"]==m) for r in provider_reports]
        os=[x["omega_hat"] for x in xs]; ks=[x["kD"] for x in xs]
        ok=_rel_span(os)<=float(cfg["cross_provider_agreement"]["omega_hat_relative_span_max"]) and _rel_span(ks)<=float(cfg["cross_provider_agreement"]["kD_relative_span_max"])
        if ok:
            agreed.append({"mode_m":m,"omega_hat":float(np.median(os)),"kD":float(np.median(ks)),
                           "omega_provider_span":_rel_span(os),"kD_provider_span":_rel_span(ks)})
    rpo_all=bool(provider_reports) and all(r["rpo_accepted"] for r in provider_reports)
    min_providers=int(cfg["cross_provider_agreement"].get("minimum_provider_count",2))
    provider_count_ok=len(provider_reports)>=min_providers and coverage.get("status")=="FULL_PROVIDER_SET"
    dimensionless_ok=bool(provider_count_ok and rpo_all and len(agreed)>=int(cfg["cross_provider_agreement"]["minimum_common_qualified_modes"]))
    # True relative-return Floquet monodromy: only after dimensionless gate.
    floquet=[]
    if dimensionless_ok and bool(cfg["true_floquet"]["enabled"]):
        Nf=int(cfg["true_floquet"]["resolution"])
        for p in providers:
            pg=p["anchor"].get("provider_group"); cen,nm=p["sample"](Nf)
            rr=c006["orbit"].search_relative_periodic_orbit(
                cen,D=1.0,offset_over_D=float(cfg["offset_over_D"]),eps_over_D=float(cfg["eps_over_D"]),
                channel_phase=float(cfg["channel_phase_rad"]),gamma_plus=float(cfg["gamma_plus_hat"]),
                gamma_minus=float(cfg["gamma_minus_hat"]),dt_hat=float(cfg["true_floquet"]["rpo_dt_hat"]),
                max_time_hat=float(cfg["true_floquet"]["rpo_max_time_hat"]),min_time_hat=float(cfg["rpo_conditioning"]["min_time_hat"]),
                snapshot_stride=int(cfg["rpo_conditioning"]["snapshot_stride"]),
                recurrence_tol_over_D=float(cfg["rpo_conditioning"]["recurrence_tol_over_D"]),
                force_python=bool(force_python),skip_build=True,return_trajectory=False)
            cand=rr["candidate"]
            if not cand.get("accepted",False):
                floquet.append({"provider_group":pg,"accepted":False,"reason":"FLOQUET_RESOLUTION_RPO_FAIL"}); continue
            full=c006["monodromy"].full_relative_monodromy_fd(
                rr["initial_state"],D=1.0,period_hat=float(cand["period_hat"]),dt_hat=float(cfg["true_floquet"]["integration_dt_hat"]),
                shift=int(cand["shift"]),rotation=np.asarray(cand["rotation"],float),
                translation=np.asarray(cand["translation_over_D"],float),
                eps_over_D=float(cfg["eps_over_D"]),gamma_plus=float(cfg["gamma_plus_hat"]),
                gamma_minus=float(cfg["gamma_minus_hat"]),fd_step_over_D=float(cfg["true_floquet"]["fd_step_over_D"]),
                max_n=int(cfg["true_floquet"]["max_n"]),force_python=bool(force_python),skip_build=True)
            kel=c006["monodromy"].kelvin_restricted_true_monodromy(full,cen,rr["initial_state"])
            ev=np.asarray(kel["kelvin_eigenvalues"],complex)
            moddev=float(np.max(np.abs(np.abs(ev)-1.0)))
            passq=(float(full["base_relative_map_residual"])<=float(cfg["true_floquet"]["base_map_residual_max"])
                   and float(full["time_tangent_neutral_residual"])<=float(cfg["true_floquet"]["neutral_residual_max"])
                   and float(kel["kelvin_subspace_leakage"])<=float(cfg["true_floquet"]["subspace_leakage_max"])
                   and moddev<=float(cfg["true_floquet"]["multiplier_modulus_deviation_max"]))
            floquet.append({"provider_group":pg,"accepted":bool(passq),"phase_turns":float(kel["true_floquet_phase_turns"]),
                            "subspace_leakage":float(kel["kelvin_subspace_leakage"]),
                            "base_relative_map_residual":float(full["base_relative_map_residual"]),
                            "time_tangent_neutral_residual":float(full["time_tangent_neutral_residual"]),
                            "multiplier_modulus_deviation_max":moddev,
                            "kelvin_eigenvalues":_complex_rows(ev)})
    floquet_ok=(not cfg["true_floquet"]["required_for_particle_promotion"]) or (len(floquet)==len(providers) and all(x.get("accepted") for x in floquet))
    out.update({"rpo":rpo_rows,"providers":provider_reports,"agreed_modes":agreed,
                "provider_coverage":coverage,
                "single_provider_dynamic_completed":bool(len(provider_reports)==1),
                "dimensionless_dynamic_qualified":dimensionless_ok,
                "true_floquet":floquet,"true_floquet_qualified":bool(floquet_ok),
                "particle_promotion_qualified":bool(dimensionless_ok and floquet_ok)})
    return out
