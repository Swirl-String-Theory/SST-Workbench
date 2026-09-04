from __future__ import annotations
import argparse, copy, json, shutil, time
from pathlib import Path
from sst_thread_falsifier.campaign import run_full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config/extended.json")
    ap.add_argument("--dataset",default=r"..\..\KnotPlot\knots\final")
    ap.add_argument("--out",default=None)
    ap.add_argument("--force-python",action="store_true")
    ap.add_argument("--skip-build",action="store_true")
    ap.add_argument("--overwrite",action="store_true")
    a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding="utf-8"))
    ladder=list(cfg.get("resample_ladder",[128,256,512]))
    out=Path(a.out or f"outputs_extended_{time.strftime('%Y%m%d_%H%M%S')}")
    if out.exists() and a.overwrite: shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True)
    reports=[]
    for n in ladder:
        c=copy.deepcopy(cfg); c["resample_n"]=int(n); c.pop("resample_ladder",None)
        cp=out/f"config_N{n}.json"; cp.write_text(json.dumps(c,indent=2),encoding="utf-8")
        rep=run_full(cp,a.dataset,out/f"N{n}",a.force_python,a.skip_build)
        reports.append((int(n),rep))
    by_path={}
    for n,rep in reports:
        for d in rep["datasets"]:
            g=d["gates"]
            by_path.setdefault(d["source_path"],[]).append({
                "N":n,
                "structural_status":d["hard_structural_status"],
                "boost_null":g["G1_uniform_boost_null"]["shape_rms_over_rg"],
                "radial_response":g["G4_radial_texture_response"]["shape_rms_over_rg"],
                "director_response":g["G5_director_texture_response"]["shape_rms_over_rg"]})
    conv=[]; tol=float(cfg.get("convergence_relative_tol",0.20))
    for p,rows in by_path.items():
        rows=sorted(rows,key=lambda x:x["N"])
        status="PASS"
        if any(r["structural_status"]!="PASS" for r in rows): status="FAIL"
        rel=None
        if len(rows)>=2:
            a0=rows[-2]["radial_response"]; a1=rows[-1]["radial_response"]
            rel=abs(a1-a0)/max(abs(a1),abs(a0),1e-300)
            if rel>tol: status="FAIL"
        conv.append({"source_path":p,"rows":rows,"highest_two_radial_relative_change":rel,"tol":tol,"status":status})
    overall="PASS" if all(x["status"]=="PASS" for x in conv) else "FAIL"
    summary={"overall_extended_status":overall,"ladder":ladder,"convergence":conv,
             "interpretation":"Extended PASS requires structural null/covariance gates at every N and convergence of the conditional radial response between the two highest resolutions."}
    (out/"extended_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({"out":str(out),"overall_extended_status":overall,"ladder":ladder,"datasets":len(conv)},indent=2))
    raise SystemExit(0 if overall=="PASS" else 2)
if __name__=="__main__": main()
