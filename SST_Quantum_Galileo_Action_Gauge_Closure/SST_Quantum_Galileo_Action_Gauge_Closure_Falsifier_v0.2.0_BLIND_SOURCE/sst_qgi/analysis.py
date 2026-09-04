from __future__ import annotations
from pathlib import Path
import csv, json, math
import numpy as np

from .constants import legacy_h_echo, legacy_hbar_echo, provenance_audit
from .qgi import (
    ideal_action, generalized_action, finite_pulse_action, phase_from_action,
    lab_action_numeric, lab_action_analytic, freefall_boundary_action, fit_power_law
)
from .geometry import descriptors
from .gf_action import (
    load_fluid_provenance, rankine_specific_action,
    geometry_action_coefficients, load_absolute_fluid_scale, absolute_rankine_action
)

def dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _relerr(a,b):
    return abs(a-b)/max(abs(b),1e-300)

def _write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8")
        return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def source_target_leak_scan(project_root: Path) -> dict:
    # Blind runtime may not contain a Planck target or standard h/hbar symbols.
    forbidden=("H"+"_"+"SI","H"+"BAR"+"_"+"SI","scipy.constants."+"h","physical_"+"constants")
    hits=[]
    for p in (project_root/"sst_qgi").rglob("*.py"):
        if p.name=="reveal.py":
            continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        for token in forbidden:
            if token in text:
                hits.append({"file":str(p.relative_to(project_root)),"token":token})
    return {"hits":hits,"n_hits":len(hits),"status":"PASS" if not hits else "FAIL"}

def _qgi_specific_action_status(project_root: Path, cfg: dict) -> dict:
    p=project_root/f"{cfg['project_name']}-outputs"/"blind"/"qgi_phase"/"qgi_specific_action.json"
    if not p.exists():
        return {
            "available":False,
            "status":"NOT_RUN",
            "reason":"QGI phase-preparation stage has not produced qgi_specific_action.json",
        }
    obj=load_json(p)
    return {"available":obj.get("status")=="READY",**obj}

def _fluid_specific_action_status(project_root: Path) -> dict:
    p=project_root/"data"/"fluid"/"prepared"/"independent_circulation.json"
    fp=load_fluid_provenance(p)
    if fp is None:
        return {
            "available":False,
            "clean":False,
            "status":"NOT_RUN",
            "reason":"No prepared independent circulation measurement.",
        }
    return {
        "available":True,
        "clean":fp.clean_for_specific_action,
        "status":"READY" if fp.clean_for_specific_action else "INVALID_PROVENANCE",
        "measurement_id":fp.measurement_id,
        "Gamma_m2_s":fp.gamma_m2_s,
        "sigma_Gamma_m2_s":fp.sigma_gamma_m2_s,
        "method":fp.method,
        "source":fp.source,
        "depends_on_h":fp.depends_on_h,
        "depends_on_hbar":fp.depends_on_hbar,
        "depends_on_compton_radius":fp.depends_on_compton_radius,
        "depends_on_electron_mass":fp.depends_on_electron_mass,
        "depends_on_alpha":fp.depends_on_alpha,
    }

def run_blind(cfg: dict, project_root: Path, mode: str) -> dict:
    out=project_root/f"{cfg['project_name']}-outputs"
    blind=out/"blind"
    manifest=load_json(blind/"public_manifest.json")
    phys=cfg["physics"]
    m=float(phys["mass_kg"])
    g=float(phys["g_m_s2"])
    T=np.array(phys["T_s"],dtype=float)

    # Macro action closure: no Planck target.
    S=ideal_action(T,m,g)
    p_action,A_action=fit_power_law(T,S)

    # Legacy SST near-h number: negative provenance control only.
    h_echo=legacy_h_echo()
    hbar_echo=legacy_hbar_echo()
    phase_echo=phase_from_action(S,hbar_echo)
    p_phase_echo,A_phase_echo=fit_power_law(T,phase_echo)

    ns=cfg["numerics"]["action_n_extended" if mode=="extended" else "action_n_basic"]
    action_rows=[]
    for n in ns:
        for Tv in T:
            sn=lab_action_numeric(float(Tv),m,g,int(n))
            sa=lab_action_analytic(float(Tv),m,g)
            sf=freefall_boundary_action(float(Tv),m,g)
            action_rows.append({
                "T_s":float(Tv),
                "n_time":int(n),
                "S_lab_numeric_J_s":sn,
                "S_lab_analytic_J_s":sa,
                "S_freefall_boundary_J_s":sf,
                "action_rel_error":_relerr(sn,sa),
                "frame_rel_error":_relerr(sn,sf),
            })
    finest=max(ns)
    finest_rows=[r for r in action_rows if r["n_time"]==finest]
    finest_action=max(r["action_rel_error"] for r in finest_rows)
    finest_frame=max(r["frame_rel_error"] for r in finest_rows)

    gen=generalized_action(g,T,m,g)
    gen_err=float(np.max(np.abs((gen-S)/np.maximum(np.abs(S),1e-300))))
    fp=finite_pulse_action(T,0.0,0.0,m,g)
    fp_err=float(np.max(np.abs((np.abs(fp)-np.abs(S))/np.maximum(np.abs(S),1e-300))))

    # Geometry branch: seal dimensionless geometry/action coefficients blind.
    metric_rows=[]
    hash_mismatches=0
    qualified_geometry=0
    for c in manifest["candidates"]:
        pts=np.load(blind/"geometries"/f"{c['candidate_id']}.npy",allow_pickle=False)
        d=descriptors(pts)
        if d["geometry_sha256"] != c["geometry_sha256"]:
            hash_mismatches += 1
        gc=geometry_action_coefficients(d["length"],d["thickness_radius_proxy"])
        if gc["qualified"]:
            qualified_geometry += 1
        metric_rows.append({
            "candidate_id":c["candidate_id"],
            "stratum_token":c["stratum_token"],
            "geometry_sha256":d["geometry_sha256"],
            "n_points":d["n_points"],
            "length":d["length"],
            "segment_cv":d["segment_cv"],
            "curvature_mean":d["curvature_mean"],
            "curvature_rms":d["curvature_rms"],
            "curvature_max":d["curvature_max"],
            "minrad_proxy":d["minrad_proxy"],
            "min_nonlocal_distance_proxy":d["min_nonlocal_distance_proxy"],
            "thickness_radius_proxy":d["thickness_radius_proxy"],
            **gc,
            "specific_action_geometry_dependence":"CANCELS_AT_LEADING_RANKINE_ORDER",
        })

    leak=source_target_leak_scan(project_root)
    qgi=_qgi_specific_action_status(project_root,cfg)
    fluid=_fluid_specific_action_status(project_root)

    # Primary provenance-clean closure:
    # QGI derives h/m from phase and g without mass or Planck target.
    # Rankine fluid gives h/M = Gamma/2.
    gf_specific=None
    closure=None
    if fluid.get("available") and fluid.get("clean"):
        gf_specific=rankine_specific_action(float(fluid["Gamma_m2_s"]))
    if qgi.get("available") and gf_specific is not None:
        qgi_h_over_m=float(qgi["h_over_m_m2_s"])
        gf_h_over_m=float(gf_specific["h_over_m_m2_s"])
        sigma_gf=None
        if fluid.get("sigma_Gamma_m2_s") not in (None,""):
            sigma_gf=0.5*float(fluid["sigma_Gamma_m2_s"])
        sigma_qgi=qgi.get("sigma_h_over_m_m2_s")
        sigma_qgi=None if sigma_qgi in (None,"") else float(sigma_qgi)
        sigma_delta=None
        z_score=None
        if sigma_gf is not None or sigma_qgi is not None:
            sigma_delta=math.sqrt((sigma_gf or 0.0)**2+(sigma_qgi or 0.0)**2)
            if sigma_delta>0:
                z_score=abs(gf_h_over_m-qgi_h_over_m)/sigma_delta
        closure={
            "GF_h_over_M_m2_s":gf_h_over_m,
            "sigma_GF_h_over_M_m2_s":sigma_gf,
            "QGI_h_over_m_m2_s":qgi_h_over_m,
            "sigma_QGI_h_over_m_m2_s":sigma_qgi,
            "relative_error":_relerr(gf_h_over_m,qgi_h_over_m),
            "ratio_GF_over_QGI":gf_h_over_m/qgi_h_over_m,
            "combined_sigma_m2_s":sigma_delta,
            "difference_z_score":z_score,
            "mass_used":False,
            "kg_used":False,
            "planck_target_used":False,
        }

    # Optional absolute action branch: geometry enters here. It is secondary because
    # SI kg metrology is not independent of h after the 2019 SI redefinition.
    abs_scale=load_absolute_fluid_scale(project_root/"data"/"fluid"/"prepared"/"absolute_fluid_scale.json")
    abs_rows=[]
    if abs_scale is not None and fluid.get("available") and fluid.get("clean"):
        for r in metric_rows:
            if not r["qualified"]:
                continue
            a=absolute_rankine_action(
                float(abs_scale["rho_kg_m3"]),
                float(fluid["Gamma_m2_s"]),
                float(abs_scale["a_core_m"]),
                float(r["Lhat_radius"]),
            )
            abs_rows.append({
                "candidate_id":r["candidate_id"],
                "stratum_token":r["stratum_token"],
                "Lhat_radius":r["Lhat_radius"],
                **a,
                "clean_model_provenance":bool(abs_scale["clean_model_provenance"]),
                "metrology_independent_of_h":False,
            })

    thr=cfg["gates"][mode]
    gates={
        "G1_ACTION_CUBIC_EXPONENT":{
            "status":"PASS" if abs(p_action-3.0)<=thr["cubic_exponent_abs"] else "FAIL",
            "value":abs(p_action-3.0),
            "threshold":thr["cubic_exponent_abs"],
        },
        "G2_NUMERIC_LAB_ACTION":{
            "status":"PASS" if finest_action<=thr["action_rel"] else "FAIL",
            "value":finest_action,
            "threshold":thr["action_rel"],
            "n_time":finest,
        },
        "G3_FRAME_GAUGE_ACTION_CLOSURE":{
            "status":"PASS" if finest_frame<=thr["frame_rel"] else "FAIL",
            "value":finest_frame,
            "threshold":thr["frame_rel"],
            "n_time":finest,
        },
        "G4_GENERALIZED_ACTION_A_EQUALS_G":{
            "status":"PASS" if gen_err<=thr["identity_rel"] else "FAIL",
            "value":gen_err,
            "threshold":thr["identity_rel"],
        },
        "G5_FINITE_PULSE_ACTION_ZERO_LIMIT":{
            "status":"PASS" if fp_err<=thr["identity_rel"] else "FAIL",
            "value":fp_err,
            "threshold":thr["identity_rel"],
        },
        "G6_BLIND_GEOMETRY_INTEGRITY":{
            "status":"PASS" if hash_mismatches==0 and qualified_geometry==len(metric_rows) else "FAIL",
            "hash_mismatches":hash_mismatches,
            "qualified_geometry":qualified_geometry,
            "n_candidates":len(metric_rows),
            "source_identity_read":False,
        },
        "G7_REVEAL_TARGET_LEAK_SCAN":leak,
        "G8_QGI_SPECIFIC_ACTION_DATA":{
            "status":(
                "PASS" if qgi.get("available") and qgi.get("source_grade")=="RAW_POPULATION_CSV"
                else "CONDITIONAL" if qgi.get("available")
                else "NOT_RUN"
            ),
            "source_grade":qgi.get("source_grade"),
            "h_over_m_m2_s":qgi.get("h_over_m_m2_s"),
            "planck_target_used":qgi.get("planck_target_used"),
            "mass_used":qgi.get("mass_used"),
            "note":qgi.get("note",qgi.get("reason")),
        },
        "G9_FLUID_CIRCULATION_PROVENANCE":{
            **fluid,
            "input_status":fluid.get("status"),
            "status":(
                "PASS" if fluid.get("available") and fluid.get("clean")
                else "INVALID" if fluid.get("available")
                else "NOT_RUN"
            ),
        },
        "G10_SPECIFIC_ACTION_CIRCULATION_CLOSURE":{
            "status":(
                "PASS"
                if closure is not None
                and qgi.get("source_grade")=="RAW_POPULATION_CSV"
                and closure["relative_error"]<=thr["specific_action_rel"]
                else "FAIL"
                if closure is not None
                and qgi.get("source_grade")=="RAW_POPULATION_CSV"
                else "CONDITIONAL_PASS"
                if closure is not None
                and closure["relative_error"]<=thr["specific_action_rel"]
                else "CONDITIONAL_FAIL"
                if closure is not None
                else "NOT_RUN"
            ),
            "threshold":thr["specific_action_rel"],
            "result":closure,
            "qgi_source_grade":qgi.get("source_grade"),
            "equation":"(h/M)_GF = Gamma/2  vs  (h/m)_QGI = pi*g_eff^2/(12*|c3|)",
        },
        "G11_RANKINE_TWO_PI_IDENTITY":{
            "status":(
                "PASS" if gf_specific is not None and gf_specific["two_pi_identity_rel"]<=thr["identity_rel"]
                else "NOT_RUN"
            ),
            "result":gf_specific,
            "note":"Internal fluid-model identity; not empirical evidence by itself.",
        },
        "G12_GEOMETRY_ACTION_COEFFICIENT_SEAL":{
            "status":"PASS" if qualified_geometry==len(metric_rows) else "FAIL",
            "n_sealed":qualified_geometry,
            "n_candidates":len(metric_rows),
            "leading_specific_action_geometry_dependence":"NONE_IN_UNIFORM_RANKINE_CORE",
            "absolute_action_geometry_dependence":"h_GF proportional to Lhat*rho*Gamma*a^3",
        },
    }

    macro_names=[f"G{i}_" for i in range(1,8)]
    macro_pass=all(
        g["status"]=="PASS"
        for name,g in gates.items()
        if any(name.startswith(prefix) for prefix in macro_names)
    )
    if closure is not None:
        g10_status=gates["G10_SPECIFIC_ACTION_CIRCULATION_CLOSURE"]["status"]
        if g10_status=="PASS":
            verdict="PROVENANCE_CLEAN_SPECIFIC_ACTION_PASS"
        elif g10_status=="FAIL":
            verdict="PROVENANCE_CLEAN_SPECIFIC_ACTION_FALSIFIED"
        elif g10_status=="CONDITIONAL_PASS":
            verdict="PUBLIC_FIGURE_SPECIFIC_ACTION_CONDITIONAL_PASS"
        else:
            verdict="PUBLIC_FIGURE_SPECIFIC_ACTION_CONDITIONAL_FAIL"
    elif macro_pass and qgi.get("available") and not fluid.get("clean"):
        verdict="STRICT_MACRO_PASS__QGI_SPECIFIC_ACTION_READY__CLEAN_FLUID_CIRCULATION_NOT_PROVIDED"
    elif macro_pass and not qgi.get("available"):
        verdict="STRICT_MACRO_PASS__QGI_PHASE_DATA_NOT_AVAILABLE"
    else:
        verdict="BLIND_FALSIFIER_HIT"

    _write_csv(blind/f"carrier_metrics_{mode}.csv",metric_rows)
    _write_csv(blind/f"action_convergence_{mode}.csv",action_rows)
    if abs_rows:
        _write_csv(blind/f"absolute_geometry_fluid_action_{mode}.csv",abs_rows)
    _write_csv(blind/f"sealed_action_prediction_{mode}.csv",[
        {
            "T_s":float(Tv),
            "action_prediction_J_s":float(Sv),
            "legacy_echo_phase_prediction_rad":float(pv),
        }
        for Tv,Sv,pv in zip(T,S,phase_echo)
    ])

    result={
        "format":"SST-QGI-GEOMETRY-FLUID-ACTION-RUN-2.0",
        "mode":mode,
        "backend":"cpp-pybind11" if _native_available() else "numpy-fallback",
        "source_identity_read":False,
        "reveal_target_read":False,
        "n_candidates":len(metric_rows),
        "action_fit":{"p":p_action,"prefactor_abs_J_s_per_s3":A_action},
        "qgi_specific_action":qgi,
        "fluid_specific_action_input":fluid,
        "specific_action_closure":closure,
        "legacy_echo_control":{
            "classification":"ALGEBRAIC_ECHO_CONTROL",
            "h_echo_J_s":h_echo,
            "hbar_echo_J_s":hbar_echo,
            "phase_fit_p":p_phase_echo,
            "phase_fit_prefactor_abs":A_phase_echo,
            "independent_prediction":False,
            "provenance":provenance_audit(),
        },
        "gates":gates,
        "blind_verdict":verdict,
        "interpretation":{
            "primary_new_gate":"specific action / circulation",
            "geometry_role":(
                "Geometry cancels from h/M at leading uniform-Rankine order; "
                "geometry is sealed for the absolute-action and future finite-core correction branches."
            ),
            "absolute_action_warning":(
                "SI kg-based absolute action is secondary because post-2019 SI mass metrology uses fixed h."
            ),
            "legacy_h_relation":"control only",
        },
    }
    dump_json(blind/f"gate_report_{mode}.json",result)
    if mode=="extended":
        _extended_sweeps(cfg,blind,m,g)
    return result

def _native_available():
    try:
        import sst_qgi_native
        return True
    except Exception:
        return False

def _extended_sweeps(cfg,blind,m,g):
    T=np.array(cfg["physics"]["T_s"],dtype=float)
    rows=[]
    for ratio in cfg["physics"]["a_over_g"]:
        a=float(ratio)*g
        S=generalized_action(a,T,m,g)
        for Tv,s in zip(T,S):
            rows.append({"a_over_g":float(ratio),"T_s":float(Tv),"action_J_s":float(s)})
    _write_csv(blind/"generalized_acceleration_action_sweep.csv",rows)

    fp_rows=[]
    for tk in cfg["physics"]["Tkick_s"]:
        for td in cfg["physics"]["Td_s"]:
            S=finite_pulse_action(T,float(tk),float(td),m,g)
            for Tv,s in zip(T,S):
                fp_rows.append({
                    "Tkick_s":float(tk),"Td_s":float(td),
                    "T_s":float(Tv),"action_J_s":float(s)
                })
    _write_csv(blind/"finite_pulse_action_sweep.csv",fp_rows)
