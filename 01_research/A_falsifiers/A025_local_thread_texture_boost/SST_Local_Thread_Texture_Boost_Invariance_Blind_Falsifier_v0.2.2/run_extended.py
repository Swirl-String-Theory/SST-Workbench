from __future__ import annotations
import argparse,copy,json,shutil,time
from pathlib import Path
from sst_thread_falsifier.campaign import run_full


def _rel(a,b):
    return abs(float(b)-float(a))/max(abs(float(a)),abs(float(b)),1e-300)


def main():
    ap=argparse.ArgumentParser(description="SST v0.2.2 fixed-core resolution ladder")
    ap.add_argument("--config",default="config/extended.json")
    ap.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    ap.add_argument("--out",default=None)
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--skip-build",action="store_true")
    ap.add_argument("--overwrite",action="store_true")
    a=ap.parse_args(); cfg=json.loads(Path(a.config).read_text(encoding="utf-8"))
    ladder=[int(x) for x in cfg.get("resample_ladder",[128,256,512])]
    out=Path(a.out or f"outputs_{Path(a.config).stem}_{time.strftime('%Y%m%d_%H%M%S')}")
    if out.exists() and a.overwrite: shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for n in ladder:
        c=copy.deepcopy(cfg); c["resample_n"]=n; c.pop("resample_ladder",None)
        cp=out/f"config_N{n}.json"; cp.write_text(json.dumps(c,indent=2),encoding="utf-8")
        rep=run_full(cp,a.dataset,out/f"N{n}",a.force_python,a.skip_build); reports.append((n,rep))
    by_path={}
    for n,rep in reports:
        for d in rep["datasets"]:
            g=d["gates"]
            by_path.setdefault(d["source_path"],[]).append({
                "N":n,"structural_status":d["structural_status"],"bridge_status":d["conditional_bridge_status"],
                "boost_null":g["G1_common_boost_null"]["shape_rms_over_rg"],
                "return_shape":g["G5_return_flux_locality"]["mid_far_final_shape_rms_over_rg"],
                "primary_median":g["G6_primary_bundle_dynamical_response"]["median"],
                "gradient":g["G7_density_gradient_differential_response"]["shape_rms_over_rg"],
                "secondary":g["G8_primary_secondary_superposition_response"]["shape_rms_over_rg"],
                "knot_core":d["fixed_core"]["knot_core_radius"],"thread_core":d["fixed_core"]["thread_core_radius"],
                "rg_reference":d["fixed_core"]["rg_reference"]})
    std=float(cfg.get("convergence_relative_tol_standard",0.05)); cert=float(cfg.get("convergence_relative_tol_certified",0.01))
    conv=[]
    for p,rows in by_path.items():
        rows=sorted(rows,key=lambda x:x["N"]); structural=all(r["structural_status"]=="PASS" for r in rows)
        rels={"primary_median":None,"gradient":None,"secondary":None}; core_spread=0.0
        if len(rows)>=2:
            for k in rels: rels[k]=_rel(rows[-2][k],rows[-1][k])
            kvals=[r["knot_core"] for r in rows]; tvals=[r["thread_core"] for r in rows]
            core_spread=max((max(kvals)-min(kvals))/max(max(map(abs,kvals)),1e-300),(max(tvals)-min(tvals))/max(max(map(abs,tvals)),1e-300))
        worst=max([x for x in rels.values() if x is not None] or [0.0])
        tier="CERTIFIED_PASS" if structural and worst<=cert and core_spread<=1e-12 else "STANDARD_PASS" if structural and worst<=std and core_spread<=1e-12 else "FAIL"
        conv.append({"source_path":p,"rows":rows,"highest_two_relative_changes":rels,"worst_relative_change":worst,
                     "fixed_core_relative_spread":core_spread,"standard_tol":std,"certified_tol":cert,
                     "G10_fixed_core_resolution_convergence":tier})
    overall="PASS" if all(x["G10_fixed_core_resolution_convergence"]!="FAIL" for x in conv) else "FAIL"
    summary={"overall_extended_status":overall,"ladder":ladder,"convergence":conv,
             "interpretation":"G10 holds the reference-Rg core radii fixed while N changes; PASS requires structural G0-G5 at every N plus convergence of the nonlinear primary, gradient and secondary thread responses."}
    (out/"extended_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"out":str(out),"overall_extended_status":overall,"ladder":ladder,"datasets":len(conv)},indent=2))
    raise SystemExit(0 if overall=="PASS" else 2)
if __name__=="__main__": main()
