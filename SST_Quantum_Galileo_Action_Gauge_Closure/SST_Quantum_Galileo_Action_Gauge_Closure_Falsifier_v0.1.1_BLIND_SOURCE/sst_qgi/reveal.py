from __future__ import annotations
from pathlib import Path
import csv, json, math
import numpy as np
from .blind import verify_private_key

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _dump(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def _read_csv(path):
    with Path(path).open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def _write_csv(path,rows):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8")
        return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def _infer_hbar_from_phase_data(path: Path, m: float, g: float):
    rows=_read_csv(path)
    vals=[]
    out=[]
    for r in rows:
        T=float(r["T_s"])
        phi=float(r["phase_rad"])
        if phi==0:
            continue
        hbar=-(m*g*g*T**3)/(3.0*phi)
        sigma_phi=float(r.get("sigma_phase_rad") or 0.0)
        sigma_hbar=abs(hbar*sigma_phi/phi) if sigma_phi>0 else None
        vals.append((hbar,sigma_hbar))
        out.append({
            **r,
            "hbar_inferred_J_s":hbar,
            "sigma_hbar_J_s":sigma_hbar,
        })
    if not vals:
        return None,out

    weighted=[v for v in vals if v[1] is not None and v[1]>0]
    if weighted:
        w=np.array([1.0/s**2 for _,s in weighted],float)
        x=np.array([v for v,_ in weighted],float)
        mean=float(np.sum(w*x)/np.sum(w))
        sigma=float(math.sqrt(1.0/np.sum(w)))
    else:
        x=np.array([v for v,_ in vals],float)
        mean=float(np.mean(x))
        sigma=float(np.std(x,ddof=1)/math.sqrt(len(x))) if len(x)>1 else None
    return {"hbar_inferred_J_s":mean,"sigma_hbar_J_s":sigma,"n":len(vals)},out

def reveal(project_root: Path, cfg: dict) -> dict:
    out=project_root/f"{cfg['project_name']}-outputs"
    blind=out/"blind"
    rev=out/"revealed"
    rev.mkdir(parents=True,exist_ok=True)

    manifest=_load(blind/"public_manifest.json")
    private=_load(project_root/"private"/"reveal_key.json")
    if not verify_private_key(manifest,private):
        raise RuntimeError("Reveal-key commitment mismatch")

    target_path=project_root/"reveal"/"reveal_target.json"
    if not target_path.exists():
        raise RuntimeError(
            "Missing reveal/reveal_target.json. Extract the separate REVEAL_KEY archive "
            "only after the blind outputs have been sealed."
        )
    target=_load(target_path)
    h_target=float(target["h_J_s"])
    hbar_target=h_target/(2.0*math.pi)

    mapping={r["candidate_id"]:r for r in private["mapping"]}
    rows=[]
    for c in manifest["candidates"]:
        m=mapping[c["candidate_id"]]
        rows.append({
            **c,
            **{k:v for k,v in m.items() if k!="constructor_parameters"},
            "constructor_parameters_json":json.dumps(m["constructor_parameters"],sort_keys=True),
        })
    _write_csv(rev/"revealed_manifest.csv",rows)

    extended=_load(blind/"gate_report_extended.json")
    echo=extended["legacy_echo_control"]
    h_echo=float(echo["h_echo_J_s"])
    echo_rel=h_echo/h_target-1.0

    source_names=sorted({r["source_family"] for r in rows})
    has_shader=("shader_derived" in source_names or "shader_derived_external" in source_names)
    has_relaxed=("relaxed" in source_names)

    phys=cfg["physics"]
    phase_data_path=project_root/"reveal"/"qgi_phase_data.csv"
    empirical=None
    empirical_rows=[]
    if phase_data_path.exists():
        empirical,empirical_rows=_infer_hbar_from_phase_data(
            phase_data_path,
            float(phys["mass_kg"]),
            float(phys["g_m_s2"]),
        )
        _write_csv(rev/"qgi_empirical_hbar_inference.csv",empirical_rows)

    gates={
        "R1_SOURCE_FAMILY_COVERAGE":{
            "status":"PASS" if has_shader and has_relaxed else "FAIL",
            "shader_present":has_shader,
            "relaxed_present":has_relaxed,
            "source_families":source_names,
        },
        "R2_LEGACY_ACTION_ECHO":{
            "status":"CONTROL_ONLY",
            "h_echo_J_s":h_echo,
            "h_target_J_s":h_target,
            "fractional_difference":echo_rel,
            "independent_prediction":False,
            "classification":"ALGEBRAIC_ECHO_NOT_EVIDENCE",
        },
        "R3_EMPIRICAL_QGI_ACTION_QUANTUM":{
            "status":"PASS" if empirical is not None else "NOT_RUN_NO_RAW_PHASE_DATA",
            "result":empirical,
            "hbar_reveal_target_J_s":hbar_target if empirical is not None else None,
            "note":(
                "Independent QGI action-quantum inference requires measured phase-vs-time "
                "data that were not generated using hbar as an input."
            ),
        },
        "R4_PROVENANCE_CLEAN_SST_PLANCK_PREDICTION":{
            "status":"NOT_QUALIFIED",
            "reason":(
                "The current canonical legacy chain contains hbar upstream of "
                "rho_core/F_swirl. The near-h relation cannot count as a blind SST prediction."
            ),
        },
    }

    blind_pass=extended["blind_verdict"]=="STRICT_TARGET_BLIND_MACRO_ACTION_PASS"
    verdict=(
        "STRICT_MACRO_ACTION_GAUGE_CLOSURE_PASS__PLANCK_PREDICTION_NOT_PROVENANCE_INDEPENDENT"
        if blind_pass else "FALSIFIER_HIT"
    )

    report={
        "format":"SST-QGI-REVEALED-1.1",
        "commitment_verified":True,
        "reveal_target_was_separate":True,
        "gates":gates,
        "verdict":verdict,
        "interpretation":{
            "macro_action_gauge_closure":"tested",
            "legacy_h_relation":"algebraic echo control only",
            "independent_planck_prediction":"not established",
            "next_required_step":(
                "derive an action quantum from provenance-clean SST/knot observables "
                "without h/hbar upstream"
            ),
        },
    }
    _dump(rev/"gate_report_revealed.json",report)
    (rev/"FINAL_ASSESSMENT.md").write_text(
        "# Final assessment\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        "The blind stage never reads the Planck target. The legacy near-h relation is "
        "explicitly rejected as independent evidence because hbar occurs upstream in its "
        "legacy derivation chain.\n",
        encoding="utf-8",
    )
    return report
