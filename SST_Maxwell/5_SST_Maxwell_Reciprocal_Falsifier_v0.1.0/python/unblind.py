from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sst_reciprocal.io import load_json, dump_json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("results"); ap.add_argument("private_key"); ap.add_argument("--out",default="unblinded_summary.json"); args=ap.parse_args()
    rdir=Path(args.results); key=load_json(args.private_key)
    rows=[]
    for p in sorted(rdir.glob("CASE_*/metrics.json")):
        m=load_json(p); cid=m["case_id"]; k=key["cases"].get(cid,{})
        rows.append({"case_id":cid,"label":k.get("original_label","UNKNOWN"),"group":k.get("group","UNKNOWN"),"status":m.get("status"),
          "equilibrium_gate":m.get("gates",{}).get("equilibrium_gate"),"closure_gate":m.get("gates",{}).get("local_reciprocal_closure_gate"),
          "near_singular_gate":m.get("gates",{}).get("near_singular_gate"),"rank":m.get("svd",{}).get("rank"),
          "right_nullity":m.get("svd",{}).get("right_nullity"),"left_nullity_minus_rigid":m.get("mechanism_audit",{}).get("left_nullity_minus_rigid"),
          "positive_self_stress":m.get("positive_self_stress",{}).get("feasible"),"chi_kkt":m.get("nnls",{}).get("chi_kkt")})
    dump_json(args.out,{"unblinded":True,"rows":rows})
    print(f"Wrote {args.out}")
if __name__=="__main__": main()
