from __future__ import annotations
from pathlib import Path
import json,os
import numpy as np

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))
TOL=float(os.environ.get("SST_RESUME_REL_TOL","2e-5"))

def xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for tok in raw.replace(","," ").split():
            try: vals.append(float(tok))
            except: pass
        if len(vals)>=3: rows.append(vals[:3])
    a=np.asarray(rows,float)
    if len(a)<8: raise ValueError(f"bad XYZ: {p}")
    return a

def length(a):
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def rg(a):
    c=a-a.mean(axis=0,keepdims=True)
    return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def rel(a,b):
    return abs(a-b)/max(abs(a),abs(b),1e-300)

def main():
    rows=[]
    bad=[]
    for s in D["settings"]:
        rid=f"K31__{s['id']}"
        a=xyz(ROOT/"out"/f"{rid}_i30000.txt")
        b=xyz(ROOT/"analysis/resume_checks"/f"{rid}_i30000_resumecheck.txt")
        L0,L1=length(a),length(b)
        R0,R1=rg(a),rg(b)
        rL=rel(L0,L1);rR=rel(R0,R1)
        ok=(len(a)==len(b) and rL<=TOL and rR<=TOL)
        rec={
            "run_id":rid,"n_original":len(a),"n_reloaded":len(b),
            "length_original":L0,"length_reload":L1,"rel_length":rL,
            "rg_original":R0,"rg_reload":R1,"rel_rg":rR,
            "tolerance":TOL,"pass":ok
        }
        rows.append(rec)
        if not ok:bad.append(rec)
    payload={
        "format":"TREFOIL-V021-METRIC-NEUTRAL-RESUME-CHECK-1.0",
        "overall":"PASS" if not bad else "FAIL",
        "tolerance":TOL,"rows":rows
    }
    (ROOT/"analysis/RESUME_CONTINUITY.json").write_text(
        json.dumps(payload,indent=2)+"\n",encoding="utf-8"
    )
    print(f"RESUME CONTINUITY: {'PASS' if not bad else 'FAIL'} {len(rows)-len(bad)}/{len(rows)}")
    if bad:
        for x in bad[:10]:
            print(x["run_id"],"relL=",x["rel_length"],"relRg=",x["rel_rg"])
        return 4
    return 0

if __name__=="__main__":
    raise SystemExit(main())
