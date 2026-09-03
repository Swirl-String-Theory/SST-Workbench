from __future__ import annotations
from pathlib import Path
import csv, json, statistics
from .blind import verify_private_key

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def _dump(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")

def _read_csv(path):
    with Path(path).open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def _write_csv(path,rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def reveal(project_root: Path, cfg: dict) -> dict:
    out=project_root/f"{cfg['project_name']}-outputs"
    blind=out/"blind"; rev=out/"revealed"
    rev.mkdir(parents=True,exist_ok=True)
    manifest=_load(blind/"public_manifest.json")
    private=_load(project_root/"private"/"reveal_key.json")
    if not verify_private_key(manifest,private):
        raise RuntimeError("Reveal-key commitment mismatch")

    mapping={r["candidate_id"]:r for r in private["mapping"]}
    rows=[]
    for c in manifest["candidates"]:
        m=mapping[c["candidate_id"]]
        rows.append({**c,**{k:v for k,v in m.items() if k!="constructor_parameters"},
                     "constructor_parameters_json":json.dumps(m["constructor_parameters"],sort_keys=True)})
    _write_csv(rev/"revealed_manifest.csv",rows)

    metrics_path=blind/"carrier_metrics_extended.csv"
    if not metrics_path.exists():
        metrics_path=blind/"carrier_metrics_basic.csv"
    metrics=_read_csv(metrics_path)
    by_id={r["candidate_id"]:r for r in metrics}
    source_rows=[]
    groups={}
    for r in rows:
        fam=r["source_family"]
        groups.setdefault(fam,[]).append(by_id[r["candidate_id"]])
    for fam,items in sorted(groups.items()):
        source_rows.append({
            "source_family":fam,
            "n":len(items),
            "mean_segment_cv":sum(float(x["segment_cv"]) for x in items)/len(items),
            "mean_curvature_rms":sum(float(x["curvature_rms"]) for x in items)/len(items),
            "mean_phase_prefactor_rel_error_sst_vs_si":
                sum(float(x["phase_prefactor_rel_error_sst_vs_si"]) for x in items)/len(items),
        })
    _write_csv(rev/"source_family_comparison.csv",source_rows)

    source_names=set(groups)
    has_shader=("shader_derived" in source_names or "shader_derived_external" in source_names)
    has_relaxed=("relaxed" in source_names)
    coverage=has_shader and has_relaxed

    # Phase model deliberately ignores geometry in v0.1.0, so this is an audit, not evidence.
    phase_means=[float(r["mean_phase_prefactor_rel_error_sst_vs_si"]) for r in source_rows]
    spread=max(phase_means)-min(phase_means) if phase_means else 0.0

    blind_reports=[]
    for mode in ("basic","extended"):
        p=blind/f"gate_report_{mode}.json"
        if p.exists():
            blind_reports.append(_load(p))
    blind_pass=all(r["blind_verdict"]=="BLIND_MACRO_CLOSURE_PASS" for r in blind_reports)

    gates={
        "G8_SOURCE_FAMILY_COVERAGE":{
            "status":"PASS" if coverage else "FAIL",
            "shader_present":has_shader,
            "relaxed_present":has_relaxed,
            "source_families":sorted(source_names),
        },
        "G9_SOURCE_PHASE_INVARIANCE_AUDIT":{
            "status":"PASS" if spread<=1e-15 else "FAIL",
            "cross_source_spread":spread,
            "note":"Expected by construction in v0.1.0 because geometry is not coupled to QGI phase."
        }
    }
    if blind_pass and coverage and gates["G9_SOURCE_PHASE_INVARIANCE_AUDIT"]["status"]=="PASS":
        verdict="MACRO_ACTION_GAUGE_CLOSURE_PASS__KNOT_MICRODYNAMICS_UNTESTED"
    elif blind_pass and not coverage:
        verdict="DATASET_INCOMPLETE__RELAXED_SOURCE_MISSING"
    else:
        verdict="FALSIFIER_HIT"

    report={
        "format":"SST-QGI-REVEALED-1.0",
        "commitment_verified":True,
        "private_secret_packaged":False,
        "source_families":sorted(source_names),
        "gates":gates,
        "verdict":verdict,
        "interpretation":{
            "macro_closure":"tested",
            "sst_action_scale_precision":"tested only against QGI few-percent compatibility",
            "knot_microdynamic_coupling":"not defined/not tested",
            "evidence_for_sst":"not established by this package"
        }
    }
    _dump(rev/"gate_report_revealed.json",report)
    (rev/"FINAL_ASSESSMENT.md").write_text(
        "# Final assessment\n\n"
        f"**Verdict:** `{verdict}`\n\n"
        "v0.1.0 tests macro action/gauge closure and dataset integrity. "
        "It does not insert or infer a microscopic knot-to-QGI coupling.\n",
        encoding="utf-8"
    )
    return report
