from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"));G=D["overlap_calibration"]

def xyz(p):
    rows=[]
    for l in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        v=[]
        for x in l.replace(","," ").split():
            try:v.append(float(x))
            except:pass
        if len(v)>=3:rows.append(v[:3])
    a=np.asarray(rows,float)
    if len(a)<8:raise ValueError(p)
    return a
def L(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def R(a):
    b=a-a.mean(0);return float(np.sqrt(np.mean(np.sum(b*b,axis=1))))
def metrics(p0,p1):
    a=xyz(p0);b=xyz(p1);l0,l1=L(a),L(b);r0,r1=R(a),R(b)
    dl=l1/l0-1;dr=r1/r0-1;return {"dL":dl,"dRg":dr,"E":.5*(dl+dr)}
def crossing(a,b):
    if a["E"]*b["E"]>=0:return None
    f=-a["E"]/(b["E"]-a["E"])
    return a["t"]+f*(b["t"]-a["t"])

frozen=ROOT/"reference/FROZEN_K31_i00000.txt"
rows=[];byid={}
for eid,qid in G["historical_map"].items():
    s=next(x for x in D["panel"] if x["id"]==eid)
    new=metrics(ROOT/"out"/f"XQHP__{eid}_i000000.txt",ROOT/"out"/f"XQHP__{eid}_i200000.txt")
    hist=metrics(frozen,ROOT/"reference/historical"/f"{qid}_i200000.txt")
    rec={"id":eid,"historical":qid,"t":s["t"],"new":new,"historical_metrics":hist,
         "abs_E_diff":abs(new["E"]-hist["E"]),"abs_dL_diff":abs(new["dL"]-hist["dL"]),
         "abs_dRg_diff":abs(new["dRg"]-hist["dRg"])}
    rec["pass"]=rec["abs_E_diff"]<=G["abs_E_difference_max"] and rec["abs_dL_diff"]<=G["abs_dL_difference_max"] and rec["abs_dRg_diff"]<=G["abs_dRg_difference_max"]
    rows.append(rec);byid[eid]={"t":s["t"],**new};byid[qid]={"t":s["t"],**hist}
newzero=crossing(byid["E02"],byid["E03"])
histzero=crossing(byid["Q19"],byid["Q20"])
zero_diff=None if newzero is None or histzero is None else abs(newzero-histzero)
zero_pass=newzero is not None and histzero is not None and zero_diff<=G["zero_t_difference_max"]
overall=all(x["pass"] for x in rows) and zero_pass
payload={"format":"TREFOIL-V024-OVERLAP-CALIBRATION-1.0","overall":"PASS" if overall else "FAIL",
         "rows":rows,"new_zero_200k":newzero,"historical_zero_200k":histzero,"zero_abs_difference":zero_diff,
         "gates":G}
(ROOT/"analysis/OVERLAP_CALIBRATION_200K.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
print("OVERLAP CALIBRATION",payload["overall"])
for x in rows:print(x["id"],"Eerr",x["abs_E_diff"],"dLerr",x["abs_dL_diff"],"dRgerr",x["abs_dRg_diff"],"PASS",x["pass"])
print("new zero",newzero,"historical zero",histzero,"|delta|",zero_diff)
raise SystemExit(0 if overall else 4)
