from pathlib import Path
import json,os
import numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
TOL=float(D["analysis"]["resume_rel_metric_tolerance"])

def xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try:vals.append(float(t))
            except:pass
        if len(vals)>=3:rows.append(vals[:3])
    a=np.asarray(rows,float)
    if len(a)<8:raise ValueError(p)
    return a
def length(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    c=a-a.mean(0,keepdims=True);return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))
def rel(a,b):return abs(a-b)/max(abs(a),abs(b),1e-300)

rows=[];bad=[]
for s in D["settings"]:
    rid=f"K31__{s['id']}"
    a=xyz(ROOT/"out"/f"{rid}_i60000.txt")
    b=xyz(ROOT/"analysis/resume_checks"/f"{rid}_i60000_reload.txt")
    L0,L1=length(a),length(b);R0,R1=rg(a),rg(b)
    rec={"run_id":rid,"rel_length":rel(L0,L1),"rel_rg":rel(R0,R1),
         "n_original":len(a),"n_reload":len(b),"tolerance":TOL}
    rec["pass"]=rec["n_original"]==rec["n_reload"] and rec["rel_length"]<=TOL and rec["rel_rg"]<=TOL
    rows.append(rec)
    if not rec["pass"]:bad.append(rec)
payload={"format":"TREFOIL-V022-60K-RESUME-CONTINUITY-1.0",
         "overall":"PASS" if not bad else "FAIL","tolerance":TOL,"rows":rows}
(ROOT/"analysis/RESUME_CONTINUITY_60K.json").write_text(json.dumps(payload,indent=2)+"\n")
print(f"60K RESUME CONTINUITY {'PASS' if not bad else 'FAIL'}: {len(rows)-len(bad)}/{len(rows)}")
if rows:
    print("max rel L :",max(x["rel_length"] for x in rows))
    print("max rel Rg:",max(x["rel_rg"] for x in rows))
raise SystemExit(1 if bad else 0)
