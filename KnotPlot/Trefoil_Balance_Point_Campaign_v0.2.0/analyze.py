from pathlib import Path
import json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())
TOL=float(D["analysis"]["near_zero_abs_E_per_100"])
ITS=D["checkpoints"]

def xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try: vals.append(float(t))
            except: pass
        if len(vals)>=3: rows.append(vals[:3])
    a=np.asarray(rows,float)
    if len(a)<8: raise ValueError(f"Bad XYZ {p}")
    return a
def length(a): return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    c=a-a.mean(0,keepdims=True)
    return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))
def slope(xs,ys):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*100.0
def simple_sign(x):
    return 1 if x>TOL else -1 if x<-TOL else 0

def classify(full,w1,w2):
    a,b,c=simple_sign(full),simple_sign(w1),simple_sign(w2)
    if b*c==-1:
        return "INCONSISTENT_TRANSIENT"
    if a>0:return "EXPAND"
    if a<0:return "CONTRACT"
    return "NEAR_ZERO"

def bracket(rows):
    rows=sorted(rows,key=lambda r:r["scan_value"])
    direct=[r for r in rows if r["classification"]=="NEAR_ZERO"]
    crossings=[]
    usable=[r for r in rows if r["classification"] in ("EXPAND","CONTRACT","NEAR_ZERO")]
    for a,b in zip(usable[:-1],usable[1:]):
        # Require adjacency in original sorted lane, not skipping inconsistent points.
        ia=rows.index(a);ib=rows.index(b)
        if ib!=ia+1: continue
        sa,sb=a["classification"],b["classification"]
        if {sa,sb}=={"EXPAND","CONTRACT"}:
            x1,y1=a["scan_value"],a["early_E_per_100"]
            x2,y2=b["scan_value"],b["early_E_per_100"]
            x=x1-y1*(x2-x1)/(y2-y1)
            crossings.append({
                "low_setting":a["setting"],"high_setting":b["setting"],
                "scan_coordinate":a["scan_coordinate"],
                "interpolated_zero":float(x),
                "low_value":x1,"high_value":x2,
                "low_response":y1,"high_response":y2,
            })
    status="DIRECT_NEAR_ZERO_FOUND" if direct else "ZERO_BRACKET_FOUND" if crossings else "NO_ZERO_IN_FROZEN_RANGE"
    return {"status":status,"direct_near_zero":[r["setting"] for r in direct],"crossings":crossings}

def main():
    rows=[]
    for s in D["settings"]:
        rid=f"K31__{s['id']}"
        pp=[]
        for it in ITS:
            p=ROOT/"out"/f"{rid}_i{it:05d}.txt"
            if not p.is_file(): raise SystemExit(f"ERROR missing {p}")
            a=xyz(p);pp.append({"iteration":it,"length":length(a),"rg":rg(a)})
        L0,R0=pp[0]["length"],pp[0]["rg"]
        for q in pp:q["E"]=0.5*((q["length"]/L0-1)+(q["rg"]/R0-1))
        get=lambda its:slope(its,[next(q["E"] for q in pp if q["iteration"]==i) for i in its])
        full=get([0,10,25,50,100])
        w1=get([0,25,50]);w2=get([25,50,100])
        rec={
            "setting":s["id"],"lane":s["lane"],"scan_coordinate":s["scan_coordinate"],
            "scan_value":s["scan_value"],"charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
            "early_E_per_100":full,"window1_E_per_100":w1,"window2_E_per_100":w2,
            "classification":classify(full,w1,w2),
            "E_i00250":next(q["E"] for q in pp if q["iteration"]==250),
            "E_i01000":next(q["E"] for q in pp if q["iteration"]==1000),
            "E_i10000":next(q["E"] for q in pp if q["iteration"]==10000),
            "checkpoints":pp,
        }
        rows.append(rec)

    lanes={}
    for name in D["lanes"]:
        rr=[r for r in rows if r["lane"]==name]
        lanes[name]=bracket(rr)
        lanes[name]["rows"]=sorted(rr,key=lambda r:r["scan_value"])

    # Interpolate q/h/p for the joint ray if a t crossing exists.
    ray=lanes["full_balance_ray_extended"]
    if ray["crossings"]:
        t=ray["crossings"][0]["interpolated_zero"]
        ray["interpolated_qhp"]={
            "t":t,
            "charge":15+22.27046411874018*t,
            "hooke":1+0.3563655804274017*t,
            "power":5+t,
        }
    hln=lanes["hooke_dominant_bracket"]
    if hln["crossings"]:
        h=hln["crossings"][0]["interpolated_zero"]
        hln["interpolated_qhp"]={"charge":26.13523205937009,"hooke":h,"power":5.5}

    overall = (
        "JOINT_QHP_ZERO_BRACKET_FOUND" if ray["status"] in ("ZERO_BRACKET_FOUND","DIRECT_NEAR_ZERO_FOUND")
        else "CONTRACT_REGIME_FOUND_HOOKE_ONLY" if any(r["classification"]=="CONTRACT" for r in hln["rows"])
        else "NO_CONTRACT_REGIME_IN_FROZEN_RANGE"
    )
    report={"format":"TREFOIL-BALANCE-ZERO-BRACKET-REPORT-2.0",
            "geometry":"K31 / load 3.1","overall":overall,"tolerance":TOL,
            "lanes":lanes,"rows":rows,
            "guardrail":"A sign-changing early geometric response is a balance surrogate, not yet restoring-force proof."}
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

    with (ROOT/"analysis/runs.csv").open("w",newline="",encoding="utf-8") as f:
        keys=["setting","lane","scan_coordinate","scan_value","charge","hooke","power",
              "early_E_per_100","window1_E_per_100","window2_E_per_100","classification",
              "E_i00250","E_i01000","E_i10000"]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in keys})

    md=["# Trefoil Balance Point Campaign v0.2.0 — K31 zero bracket","",
        f"**Overall: `{overall}`**","",
        "Primary signed response:",
        r"\[E(i)=\frac12[(L/L_0-1)+(R_g/R_{g0}-1)]\]",
        "",
        f"`NEAR_ZERO` threshold: |early E/100| <= {TOL:g}.",
        "",
        "## Lane results",""]
    for name,x in lanes.items():
        md += [f"### {name}",f"- Status: **{x['status']}**"]
        if x.get("interpolated_qhp"):
            md.append(f"- Interpolated q/h/p: `{x['interpolated_qhp']}`")
        if x["crossings"]:
            for c in x["crossings"]: md.append(f"- Sign crossing: `{c}`")
        if x["direct_near_zero"]:
            md.append(f"- Direct near-zero settings: `{x['direct_near_zero']}`")
        md += ["","| setting | scan | q | h | p | early E/100 | class | E@1000 | E@10000 |",
               "|---|---:|---:|---:|---:|---:|---|---:|---:|"]
        for r in x["rows"]:
            md.append(f"| {r['setting']} | {r['scan_value']:.6g} | {r['charge']:.6g} | {r['hooke']:.6g} | {r['power']:.6g} | {r['early_E_per_100']:.8g} | {r['classification']} | {r['E_i01000']:.8g} | {r['E_i10000']:.8g} |")
        md.append("")
    md += ["## Decision","",
           "- If the joint ray brackets zero: use the interpolated q/h/p as the next refinement center.",
           "- If only the hooke lane reaches CONTRACT: the contractive regime exists, but the previous joint ray is not the correct balance direction.",
           "- If neither reaches CONTRACT: extend the frozen range prospectively in a new version; do not move points post hoc.",
           "- Only after a reproducible zero is found should T(2,3) repeat the same frozen bracket as an independent embedding control."]
    (ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("OVERALL:",overall)
    for name,x in lanes.items():
        print(name,":",x["status"])
        if x.get("interpolated_qhp"): print("  q/h/p:",x["interpolated_qhp"])
    return 0
if __name__=="__main__":raise SystemExit(main())
