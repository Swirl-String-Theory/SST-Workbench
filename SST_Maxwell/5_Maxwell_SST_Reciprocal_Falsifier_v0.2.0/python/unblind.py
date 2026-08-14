from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sst_reciprocal.io import load_json,dump_json

def main():
    ap=argparse.ArgumentParser(description="Unblind frozen 5_Maxwell results."); ap.add_argument("results"); ap.add_argument("private_key"); ap.add_argument("--out",required=True); ap.add_argument("--csv",default=None); args=ap.parse_args()
    rdir=Path(args.results); key=load_json(args.private_key); rows=[]
    for p in sorted(rdir.glob("CASE_*/metrics.json")):
        m=load_json(p); cid=m.get("case_id",p.parent.name); k=key["cases"].get(cid,{}); pm=k.get("private_metrics",{}); sv=m.get("svd",{}); nn=m.get("nnls",{}); gates=m.get("gates",{}); native=m.get("native",{})
        ratio=(sv.get("sigma_min_positive",0.0)/(sv.get("sigma_max") or 1.0)) if sv else None
        rows.append({"case_id":cid,"label":k.get("original_label","UNKNOWN"),"group":k.get("group","UNKNOWN"),"status":m.get("status"),"geometry_status":m.get("geometry_status"),
          "rr_residual":pm.get("residual"),"rr_thickness":pm.get("thickness"),"rr_ropelength":pm.get("ropelength"),"rr_strutcount":pm.get("strutcount"),"rr_mr_struts":pm.get("mr_struts"),
          "active_struts":native.get("active_strut_count"),"active_kinks":native.get("active_kink_count"),"equilibrium_gate":gates.get("equilibrium_gate"),"closure_gate":gates.get("local_reciprocal_closure_gate"),
          "near_singular_gate":gates.get("near_singular_gate"),"geometry_provenance_gate":gates.get("geometry_provenance_gate"),"rank":sv.get("rank"),"right_nullity":sv.get("right_nullity"),
          "left_nullity_minus_rigid":m.get("mechanism_audit",{}).get("left_nullity_minus_rigid"),"positive_self_stress":m.get("positive_self_stress",{}).get("feasible"),"chi_kkt":nn.get("chi_kkt"),
          "max_local_closure_rel":nn.get("max_local_closure_rel"),"sigma_ratio":ratio,"elapsed_s":m.get("elapsed_s"),"robustness_status":m.get("robustness",{}).get("coordinate_perturbation_status")})
    out={"unblinded":True,"package":key.get("package"),"preset":key.get("preset"),"rows":rows}; dump_json(args.out,out)
    if args.csv:
        cp=Path(args.csv); cp.parent.mkdir(parents=True,exist_ok=True)
        fields=list(rows[0].keys()) if rows else []
        with cp.open("w",newline="",encoding="utf-8") as f:
            if fields: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f"[5_Maxwell] unblinded {len(rows)} cases -> {args.out}")
if __name__=="__main__": main()
