from pathlib import Path
import json,csv
import numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
ITS=D["checkpoints"];N=256

def read_xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try:vals.append(float(t))
            except:pass
        if len(vals)>=3:rows.append(vals[:3])
    a=np.asarray(rows,float)
    if len(a)<8:raise ValueError(f"bad XYZ {p}")
    return a

def center(a):return a-a.mean(0,keepdims=True)
def length(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    c=center(a);return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def resample(a,n=N):
    seg=np.linalg.norm(np.roll(a,-1,0)-a,axis=1)
    s=np.r_[0,np.cumsum(seg)];aa=np.vstack([a,a[0]])
    t=np.linspace(0,s[-1],n,endpoint=False)
    return np.column_stack([np.interp(t,s,aa[:,j]) for j in range(3)])

def krms(a,b):
    aa=center(a);bb=center(b);h=aa.T@bb
    u,_,vt=np.linalg.svd(h)
    if np.linalg.det(u@vt)<0:u[:,-1]*=-1
    r=u@vt
    return float(np.sqrt(np.mean(np.sum((aa@r-bb)**2,axis=1))))

def shape(a,b):
    aa=resample(a);bb=resample(b)
    best=min(krms(aa,np.roll(bb,s,0)) for s in range(N))
    return best/max((rg(aa)+rg(bb))/2,1e-30)

def slope(xs,ys):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])

def lab(x,tol=1e-5):
    return "EXPAND" if x>tol else "CONTRACT" if x<-tol else "NEAR_ZERO"

def crossings(points):
    ans=[]
    for (x1,y1,s1),(x2,y2,s2) in zip(points[:-1],points[1:]):
        if y1==0:ans.append({"estimate":x1,"between":[s1,s1]})
        elif y1*y2<0:
            ans.append({"estimate":float(x1-y1*(x2-x1)/(y2-y1)),"between":[s1,s2]})
    return ans

def main():
    rows=[];runs={}
    for v in D["variants"]:
        for s in D["settings"]:
            rid=f"{v['id']}__{s['id']}"
            pp=[]
            for it in ITS:
                p=ROOT/"out"/f"{rid}_i{it:05d}.txt"
                if not p.is_file():raise SystemExit(f"ERROR missing {p}")
                a=read_xyz(p);pp.append({"iteration":it,"length":length(a),"rg":rg(a),"_a":a})
            L0,R0=pp[0]["length"],pp[0]["rg"]
            for q in pp:q["E"]=0.5*((q["length"]/L0-1)+(q["rg"]/R0-1))
            early=[q for q in pp if q["iteration"] in D["analysis"]["early_fit_iterations"]]
            er=slope([q["iteration"] for q in early],[q["E"] for q in early])*100
            rec={"run_id":rid,"variant":v["id"],"setting":s["id"],"role":s["role"],"group":s["group"],
                 "charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
                 "early_E_per_100":er,"early_sign":lab(er),
                 "E_i01000":next(q["E"] for q in pp if q["iteration"]==1000),
                 "E_i10000":pp[-1]["E"],
                 "shape_rms_i00000_to_i10000":shape(pp[0]["_a"],pp[-1]["_a"]),
                 "checkpoints":[{k:v for k,v in q.items() if k!="_a"} for q in pp]}
            rows.append(rec);runs[(v["id"],s["id"])]=rec

    consensus=[]
    for s in D["settings"]:
        rr=[runs[(v["id"],s["id"])] for v in D["variants"]]
        consensus.append({"setting":s["id"],"role":s["role"],"charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
                          "worst_abs_early_E_per_100":max(abs(r["early_E_per_100"]) for r in rr),
                          "worst_abs_final_E":max(abs(r["E_i10000"]) for r in rr),
                          "early_signs":{r["variant"]:r["early_sign"] for r in rr},
                          "early_values":{r["variant"]:r["early_E_per_100"] for r in rr}})
    consensus.sort(key=lambda r:(r["worst_abs_early_E_per_100"],r["worst_abs_final_E"]))

    brackets={}
    for v in D["variants"]:
        qpts=sorted((runs[(v["id"],sid)]["charge"],runs[(v["id"],sid)]["early_E_per_100"],sid)
                    for sid in ("QLO","QCEN","QHI"))
        hpts=sorted((runs[(v["id"],sid)]["hooke"],runs[(v["id"],sid)]["early_E_per_100"],sid)
                    for sid in ("HLO","R50","HHI"))
        brackets.setdefault("reduced_q_bracket",{})[v["id"]]={"points":qpts,"zero_crossings":crossings(qpts)}
        brackets.setdefault("full_hooke_bracket",{})[v["id"]]={"points":hpts,"zero_crossings":crossings(hpts)}

    report={"format":"TREFOIL-BALANCE-POINT-REPORT-1.0","status":"SURROGATE_BALANCE_SEARCH_NOT_FORCE_PROOF",
            "n_runs":len(rows),"runs":rows,"consensus_ranking":consensus,"brackets":brackets,
            "best_consensus_setting":consensus[0]}
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    with (ROOT/"analysis/runs.csv").open("w",newline="",encoding="utf-8") as f:
        keys=["run_id","variant","setting","role","group","charge","hooke","power","early_E_per_100","early_sign","E_i01000","E_i10000","shape_rms_i00000_to_i10000"]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in keys})
    md=["# Trefoil Balance Point Campaign v0.1.0","",
        "> Signed geometry-response balance search; not direct force proof.","",
        "## Cross-embedding ranking","",
        "| rank | setting | q | h | p | worst |early E|/100 | K31 | T23 |",
        "|---:|---|---:|---:|---:|---:|---|---|"]
    for i,r in enumerate(consensus,1):
        md.append(f"| {i} | {r['setting']} | {r['charge']:.6g} | {r['hooke']:.6g} | {r['power']:.6g} | {r['worst_abs_early_E_per_100']:.6g} | {r['early_signs']['K31']} | {r['early_signs']['T23']} |")
    md+=["","## Bracket zero crossings",""]
    for name,bd in brackets.items():
        md.append(f"### {name}")
        for vid,x in bd.items():
            md.append(f"- `{vid}`: {x['zero_crossings'] if x['zero_crossings'] else 'no sign crossing in frozen bracket'}")
    (ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n")
    print("Best consensus:",json.dumps(consensus[0],indent=2))
if __name__=="__main__":main()
