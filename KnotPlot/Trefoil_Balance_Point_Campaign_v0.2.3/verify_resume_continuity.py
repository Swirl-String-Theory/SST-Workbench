from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text());T=D["analysis"]["resume_rel_metric_tolerance"]
def xyz(p):
    a=[]
    for l in p.read_text(errors="ignore").splitlines():
        v=[]
        for x in l.replace(","," ").split():
            try:v.append(float(x))
            except:pass
        if len(v)>=3:a.append(v[:3])
    return np.asarray(a,float)
def L(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def R(a):
    b=a-a.mean(0);return float(np.sqrt(np.mean(np.sum(b*b,axis=1))))
def rel(a,b):return abs(a-b)/max(abs(a),abs(b),1e-300)
rows=[];bad=[]
for s in D["settings"]:
    rr=f"K31__{s['id']}";a=xyz(ROOT/"out"/f"{rr}_i100000.txt");b=xyz(ROOT/"analysis/resume_checks"/f"{rr}_i100000_reload.txt")
    x={"run_id":rr,"rel_length":rel(L(a),L(b)),"rel_rg":rel(R(a),R(b)),"n_original":len(a),"n_reload":len(b)}
    x["pass"]=x["n_original"]==x["n_reload"] and x["rel_length"]<=T and x["rel_rg"]<=T;rows.append(x)
    if not x["pass"]:bad.append(x)
payload={"format":"TREFOIL-V023-100K-RESUME-CONTINUITY-1.0","overall":"PASS" if not bad else "FAIL","tolerance":T,"rows":rows}
(ROOT/"analysis/RESUME_CONTINUITY_100K.json").write_text(json.dumps(payload,indent=2)+"\n")
print("100K RESUME CONTINUITY",payload["overall"],f"{len(rows)-len(bad)}/{len(rows)}")
if rows:print("max rel L",max(x["rel_length"] for x in rows),"max rel Rg",max(x["rel_rg"] for x in rows))
raise SystemExit(1 if bad else 0)
