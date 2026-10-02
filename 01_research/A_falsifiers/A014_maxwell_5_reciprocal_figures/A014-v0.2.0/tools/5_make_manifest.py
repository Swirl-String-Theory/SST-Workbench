from __future__ import annotations
import argparse,json
from pathlib import Path

BASIC_NAMES={
 "knot_3.1_final.txt","knot_4.1_final.txt","knot_5.1_final.txt","knot_6.2_final.txt","knot_7.2_final.txt",
 "knot_10.123_final.txt","torus_2.3_final.txt","torus_2.4_final.txt","torus_2.9_final.txt"
}

def read_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def quality_status(m):
    r=m.get("residual")
    if r is None: return "ridgerunner-final-residual-unknown"
    if r<=0.0051: return "ridgerunner-polish-high-resolution-residual<=0.0051"
    if r<=0.0101: return "ridgerunner-polish-residual<=0.0101"
    if r<=0.0501: return "ridgerunner-polish-residual<=0.0501"
    return "ridgerunner-final-relaxed-residual-above-0.05"

def main():
    ap=argparse.ArgumentParser(description="Build PRIVATE manifest from KnotPlot/knots/final shared-final geometry + metrics.")
    ap.add_argument("--input-dir",required=True)
    ap.add_argument("--preset",choices=["basic","extended"],default="basic")
    ap.add_argument("--config",required=True,help="Preregistration JSON preset")
    ap.add_argument("--out",required=True)
    ap.add_argument("--include",action="append",default=[],help="Optional glob; repeatable. Overrides basic/extended selection.")
    args=ap.parse_args(); root=Path(args.input_dir).resolve(); cfg=read_json(args.config); files=sorted(root.glob("*_final.txt"))
    if args.include:
        picked=[]
        for pat in args.include: picked.extend(root.glob(pat))
        files=sorted(set(picked))
    elif args.preset=="basic": files=[p for p in files if p.name in BASIC_NAMES]
    cases=[]; missing_metrics=[]
    for p in files:
        mp=p.with_suffix(".metrics.json")
        if not mp.exists(): missing_metrics.append(p.name); continue
        m=read_json(mp); counts=[int(x) for x in m.get("vertices_per_component",[])]
        if not counts: raise RuntimeError(f"Missing vertices_per_component in {mp}")
        if sum(counts)<=0: raise RuntimeError(f"Invalid component counts in {mp}")
        thickness=float(m["thickness"]) if m.get("thickness") is not None else None
        residual=m.get("residual")
        qc_limit=float(cfg.get("max_rr_residual_for_equilibrium",0.05))
        qc_pass=(residual is not None and float(residual)<=qc_limit)
        cases.append({
          "path":str(p),"label":p.stem,"group":p.stem.replace("_final",""),"resolution":sum(counts),"component_counts":counts,
          "radius":thickness,"source_role":"knotplot-ridgerunner-shared-final-audit-geometry","geometry_status":quality_status(m),"geometry_qc_pass":qc_pass,"complete_mechanical_model":False,
          "private_metrics":{"component_count":m.get("component_count"),"residual":m.get("residual"),"residual_converged":m.get("residual_converged"),"thickness":m.get("thickness"),
                             "ropelength":m.get("ropelength"),"length":m.get("length"),"strutcount":m.get("strutcount"),"mr_struts":m.get("mr_struts"),
                             "edge_length_ratio":m.get("edge_length_ratio"),"checkpoint_tag":m.get("checkpoint_tag")}
        })
    if not cases: raise RuntimeError(f"No usable *_final.txt cases in {root}")
    obj={"package":"5_Maxwell_SST_Reciprocal_Falsifier_v0.2.0","preset":args.preset,"knots_dir":str(root),"preregistration":cfg,"cases":cases,"missing_metrics":missing_metrics}
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(obj,indent=2)+"\n",encoding="utf-8")
    print(f"[5_Maxwell] private manifest: {len(cases)} cases -> {out}")
    if missing_metrics: print(f"[5_Maxwell] skipped without metrics: {len(missing_metrics)}")

if __name__=="__main__": main()
