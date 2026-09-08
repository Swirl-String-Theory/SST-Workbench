from __future__ import annotations
import argparse,copy,hashlib,json,shutil,time
from pathlib import Path
from sst_thread_falsifier.campaign import run_full


def _canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"))
def _sha(o): return hashlib.sha256(_canonical(o).encode()).hexdigest()
def _rel(a,b): return abs(float(b)-float(a))/max(abs(float(a)),abs(float(b)),1e-300)


def _extract(d):
    g=d["gates"]
    return {
        "structural_status":d["structural_status"],"bridge_status":d["conditional_bridge_status"],
        "boost_null":g["G1_common_boost_null"]["shape_rms_over_rg"],
        "return_shape":g["G6_return_flux_locality"]["mid_far_final_shape_rms_over_rg"],
        "primary_median":g["G7_primary_bundle_dynamical_response"]["median"],
        "circulation_gradient":g["G8_density_mechanism_decomposition"]["circulation_gradient"]["shape_rms_over_rg"],
        "position_density_gradient":g["G8_density_mechanism_decomposition"]["position_density_gradient"]["shape_rms_over_rg"],
        "secondary":g["G9_primary_secondary_superposition_response"]["shape_rms_over_rg"],
        "source_far_field":g["G11_finite_source_to_parallel_limit"]["field_relative_errors"][-1],
        "source_far_shape":g["G11_finite_source_to_parallel_limit"]["final_shape_rms_over_rg"][-1],
        "knot_core":d["fixed_core"]["knot_core_radius"],"thread_core":d["fixed_core"]["thread_core_radius"],
        "rg_reference":d["fixed_core"]["rg_reference"],"dt":d["time_schedule"]["dt"],"steps":d["time_schedule"]["steps"],
        "t_final":d["time_schedule"]["t_final"],"subcycles":d["time_schedule"]["subcycles"]}


def main():
    ap=argparse.ArgumentParser(description="SST v0.3.0 spatial + temporal fixed-core certification ladder")
    ap.add_argument("--config",default="config/extended.json"); ap.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    ap.add_argument("--out",default=None); ap.add_argument("--force-python",action="store_true"); ap.add_argument("--skip-build",action="store_true"); ap.add_argument("--overwrite",action="store_true")
    a=ap.parse_args(); cfg=json.loads(Path(a.config).read_text(encoding="utf-8")); ladder=[int(x) for x in cfg.get("resample_ladder",[128,256,512])]
    if len(ladder)<2: raise SystemExit("resample_ladder requires at least two N values")
    out=Path(a.out or f"outputs_{Path(a.config).stem}_{time.strftime('%Y%m%d_%H%M%S')}")
    if out.exists() and a.overwrite: shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)

    # Freeze every numerical variant before the first physical run.
    variants=[]
    for n in ladder:
        c=copy.deepcopy(cfg); c["resample_n"]=n; c.pop("resample_ladder",None); c.pop("temporal_refinement_factor",None); variants.append((f"spatial_N{n}",c))
    refine=max(2,int(cfg.get("temporal_refinement_factor",2)))
    ct=copy.deepcopy(variants[-1][1]); ct["time_refinement_factor"]=int(ct.get("time_refinement_factor",1))*refine; variants.append((f"temporal_N{ladder[-1]}_x{refine}",ct))
    pre={"package_version":"0.3.0","created_unix":time.time(),"dataset":str(Path(a.dataset).resolve()),"base_config":cfg,
         "variants":[{"name":name,"config_sha256":_sha(c),"config":c} for name,c in variants],
         "commitment":"All spatial and temporal variants are frozen before execution; T_final is held constant and only N/time refinement changes."}
    (out/"certification_precommit.json").write_text(json.dumps(pre,indent=2),encoding="utf-8")

    reports={}
    for name,c in variants:
        cp=out/f"config_{name}.json"; cp.write_text(json.dumps(c,indent=2),encoding="utf-8")
        reports[name]=run_full(cp,a.dataset,out/name,a.force_python,a.skip_build)

    by_path={}
    for n in ladder:
        rep=reports[f"spatial_N{n}"]
        for d in rep["datasets"]: by_path.setdefault(d["source_path"],{})[f"N{n}"]=_extract(d)
    trep=reports[f"temporal_N{ladder[-1]}_x{refine}"]
    for d in trep["datasets"]: by_path.setdefault(d["source_path"],{})["temporal_refined"]=_extract(d)

    spatial_std=float(cfg.get("convergence_relative_tol_standard",0.02)); spatial_cert=float(cfg.get("convergence_relative_tol_certified",0.005))
    temporal_std=float(cfg.get("temporal_relative_tol_standard",0.01)); temporal_cert=float(cfg.get("temporal_relative_tol_certified",0.0025))
    keys=["primary_median","circulation_gradient","position_density_gradient","secondary","source_far_shape"]
    conv=[]
    for p,rows in by_path.items():
        lo=rows[f"N{ladder[-2]}"]; hi=rows[f"N{ladder[-1]}"]; tr=rows.get("temporal_refined")
        spatial_changes={k:_rel(lo[k],hi[k]) for k in keys}; temporal_changes={k:_rel(hi[k],tr[k]) for k in keys} if tr else {k:float('inf') for k in keys}
        corevals=[rows[f"N{n}"]["knot_core"] for n in ladder]; threadvals=[rows[f"N{n}"]["thread_core"] for n in ladder]
        core_spread=max((max(corevals)-min(corevals))/max(max(map(abs,corevals)),1e-300),(max(threadvals)-min(threadvals))/max(max(map(abs,threadvals)),1e-300))
        tfvals=[rows[f"N{n}"]["t_final"] for n in ladder]+([tr["t_final"]] if tr else [])
        tf_spread=(max(tfvals)-min(tfvals))/max(max(map(abs,tfvals)),1e-300)
        structural=all(rows[f"N{n}"]["structural_status"]=="PASS" for n in ladder) and bool(tr and tr["structural_status"]=="PASS")
        sworst=max(spatial_changes.values()); tworst=max(temporal_changes.values())
        c1="CERTIFIED_PASS" if structural and sworst<=spatial_cert and core_spread<=1e-12 and tf_spread<=1e-12 else "STANDARD_PASS" if structural and sworst<=spatial_std and core_spread<=1e-12 and tf_spread<=1e-12 else "FAIL"
        c2="CERTIFIED_PASS" if structural and tworst<=temporal_cert and tf_spread<=1e-12 else "STANDARD_PASS" if structural and tworst<=temporal_std and tf_spread<=1e-12 else "FAIL"
        conv.append({"source_path":p,"spatial_rows":{f"N{n}":rows[f"N{n}"] for n in ladder},"temporal_refined":tr,
                     "C1_spatial_fixed_core_convergence":c1,"spatial_relative_changes_highest_two":spatial_changes,"spatial_worst_relative_change":sworst,
                     "C2_temporal_RK4_convergence":c2,"temporal_relative_changes_at_highest_N":temporal_changes,"temporal_worst_relative_change":tworst,
                     "fixed_core_relative_spread":core_spread,"T_final_relative_spread":tf_spread,
                     "thresholds":{"spatial_standard":spatial_std,"spatial_certified":spatial_cert,"temporal_standard":temporal_std,"temporal_certified":temporal_cert}})
    overall="PASS" if all(x["C1_spatial_fixed_core_convergence"]!="FAIL" and x["C2_temporal_RK4_convergence"]!="FAIL" for x in conv) else "FAIL"
    summary={"overall_extended_status":overall,"spatial_ladder":ladder,"temporal_refinement_factor":refine,"convergence":conv,
             "interpretation":"C1 tests spatial convergence with fixed core and constant T_final. C2 independently halves/refines the RK4 time step at the highest N. ds^2 subcycling may increase substeps but never changes T_final."}
    (out/"extended_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"out":str(out),"overall_extended_status":overall,"spatial_ladder":ladder,"temporal_refinement_factor":refine,"datasets":len(conv)},indent=2))
    raise SystemExit(0 if overall=="PASS" else 2)
if __name__=="__main__": main()
