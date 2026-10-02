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

    mapping={r["candidate_id"]:r for r in private["mapping"]}
    revealed_rows=[]
    for c in manifest["candidates"]:
        m=mapping[c["candidate_id"]]
        revealed_rows.append({
            **c,
            **{k:v for k,v in m.items() if k!="constructor_parameters"},
            "constructor_parameters_json":json.dumps(m["constructor_parameters"],sort_keys=True),
        })
    _write_csv(rev/"revealed_manifest.csv",revealed_rows)

    extended=_load(blind/"gate_report_extended.json")
    echo=extended["legacy_echo_control"]
    h_echo=float(echo["h_echo_J_s"])

    source_names=sorted({r["source_family"] for r in revealed_rows})
    has_shader=("shader_derived" in source_names or "shader_derived_external" in source_names)
    has_relaxed=("relaxed" in source_names)

    # Reveal geometry source-family summaries without selecting a post-hoc "best knot".
    metrics=_read_csv(blind/"carrier_metrics_extended.csv")
    by_id={r["candidate_id"]:r for r in revealed_rows}
    grouped={}
    for r in metrics:
        fam=by_id[r["candidate_id"]]["source_family"]
        grouped.setdefault(fam,[]).append(r)
    source_summary=[]
    for fam,items in sorted(grouped.items()):
        vals=lambda key:np.array([float(x[key]) for x in items],float)
        source_summary.append({
            "source_family":fam,
            "n":len(items),
            "mean_Lhat_radius":float(np.mean(vals("Lhat_radius"))),
            "median_Lhat_radius":float(np.median(vals("Lhat_radius"))),
            "mean_curvature_rms":float(np.mean(vals("curvature_rms"))),
            "mean_thickness_radius_proxy":float(np.mean(vals("thickness_radius_proxy"))),
        })
    _write_csv(rev/"source_family_geometry_summary.csv",source_summary)

    qgi=extended.get("qgi_specific_action",{})
    qgi_target_compare=None
    if qgi.get("available") and qgi.get("h_over_m_m2_s") is not None:
        rb_mass=float(cfg["physics"]["mass_kg"])
        target_h_over_m=h_target/rb_mass
        measured=float(qgi["h_over_m_m2_s"])
        qgi_target_compare={
            "QGI_h_over_m_m2_s":measured,
            "SI_reveal_h_over_Rb_mass_m2_s":target_h_over_m,
            "fractional_difference":measured/target_h_over_m-1.0,
            "note":(
                "Reveal-only benchmark. The primary blind QGI inference did not use mass or h. "
                "This comparison introduces the SI Planck target and the Rb mass only after sealing."
            ),
        }

    # Optional absolute geometry/fluid branch.
    abs_path=blind/"absolute_geometry_fluid_action_extended.csv"
    abs_summary=None
    if abs_path.exists():
        abs_rows=_read_csv(abs_path)
        joined=[]
        for r in abs_rows:
            fam=by_id[r["candidate_id"]]["source_family"]
            hgf=float(r["h_GF_J_s"])
            joined.append({
                **r,
                "source_family":fam,
                "h_target_J_s":h_target,
                "fractional_difference_vs_h":hgf/h_target-1.0,
            })
        _write_csv(rev/"absolute_geometry_fluid_action_revealed.csv",joined)
        vals=np.array([float(r["fractional_difference_vs_h"]) for r in joined],float)
        abs_summary={
            "n":len(joined),
            "median_fractional_difference":float(np.median(vals)),
            "min_fractional_difference":float(np.min(vals)),
            "max_fractional_difference":float(np.max(vals)),
            "metrology_independent_of_h":False,
            "note":(
                "Secondary model-provenance branch only. Absolute SI kg-based action is not "
                "metrology-independent of h in the post-2019 SI."
            ),
        }

    primary_gate=extended["gates"].get("G10_SPECIFIC_ACTION_CIRCULATION_CLOSURE",{})
    if primary_gate.get("status") in ("PASS","FAIL","CONDITIONAL_PASS","CONDITIONAL_FAIL"):
        primary_status=primary_gate.get("status")
    else:
        primary_status="NOT_RUN"

    gates={
        "R1_SOURCE_FAMILY_COVERAGE":{
            "status":"PASS" if has_shader and has_relaxed else "FAIL",
            "shader_present":has_shader,
            "relaxed_present":has_relaxed,
            "source_families":source_names,
        },
        "R2_PROVENANCE_CLEAN_SPECIFIC_ACTION_GATE":{
            "status":primary_status,
            "blind_result":primary_gate,
            "note":"This result was fixed before the Planck reveal target was opened.",
        },
        "R3_QGI_SPECIFIC_ACTION_VS_SI_REVEAL":{
            "status":"DIAGNOSTIC" if qgi_target_compare is not None else "NOT_RUN",
            "result":qgi_target_compare,
        },
        "R4_LEGACY_ACTION_ECHO":{
            "status":"CONTROL_ONLY",
            "h_echo_J_s":h_echo,
            "h_target_J_s":h_target,
            "fractional_difference":h_echo/h_target-1.0,
            "independent_prediction":False,
            "classification":"ALGEBRAIC_ECHO_NOT_EVIDENCE",
        },
        "R5_ABSOLUTE_GEOMETRY_FLUID_ACTION":{
            "status":"SECONDARY_METROLOGY_DEPENDENT" if abs_summary is not None else "NOT_RUN",
            "result":abs_summary,
        },
        "R6_PROVENANCE_CLEAN_ABSOLUTE_PLANCK_PREDICTION":{
            "status":"NOT_QUALIFIED",
            "reason":(
                "The primary clean observable in v0.2.0 is specific action h/m in m^2/s. "
                "An absolute SI J s prediction requires an independently justified mass/density "
                "scale and is not metrology-independent of fixed h under the post-2019 SI."
            ),
        },
    }

    if primary_status=="PASS":
        verdict="PROVENANCE_CLEAN_SPECIFIC_ACTION_CIRCULATION_PASS"
    elif primary_status=="FAIL":
        verdict="PROVENANCE_CLEAN_SPECIFIC_ACTION_CIRCULATION_FALSIFIED"
    elif primary_status=="CONDITIONAL_PASS":
        verdict="PUBLIC_FIGURE_SPECIFIC_ACTION_CONDITIONAL_PASS"
    elif primary_status=="CONDITIONAL_FAIL":
        verdict="PUBLIC_FIGURE_SPECIFIC_ACTION_CONDITIONAL_FAIL"
    else:
        verdict="MACRO_CLOSURE_PASS__PRIMARY_GEOMETRY_FLUID_ACTION_GATE_NOT_RUN"

    report={
        "format":"SST-QGI-GF-REVEALED-2.0",
        "commitment_verified":True,
        "reveal_target_was_separate":True,
        "gates":gates,
        "verdict":verdict,
        "interpretation":{
            "primary_observable":"specific action h/m [m^2/s]",
            "primary_fluid_prediction":"h/M = Gamma/2 for the preregistered uniform Rankine core",
            "geometry_null_result":(
                "At leading Rankine order, length/core geometry cancels from h/M. "
                "Geometry remains predictive for absolute action and for future derived finite-core corrections."
            ),
            "legacy_h_relation":"algebraic echo control only",
        },
    }
    _dump(rev/"gate_report_revealed.json",report)
    (rev/"FINAL_ASSESSMENT.md").write_text(
        "# Final assessment\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        "The primary v0.2.0 comparison is the target-blind specific-action/circulation gate. "
        "The SI Planck target is used only in reveal diagnostics.\n",
        encoding="utf-8",
    )
    return report
