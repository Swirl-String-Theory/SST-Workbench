from pathlib import Path
import json,csv
import numpy as np
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text());A=D["analysis"]
ET=float(A["late_zero_abs_E_tolerance"]);DT=float(A["late_drift_abs_per_1000_tolerance"]);ST=float(A["late_span_tolerance"])
def xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try:vals.append(float(t))
            except:pass
        if len(vals)>=3:rows.append(vals[:3])
    return np.asarray(rows,float)
def length(a):return float(np.linalg.norm(np.roll(a,-1,0)-a,axis=1).sum())
def rg(a):
    c=a-a.mean(0,keepdims=True);return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))
def slope(xs,ys,scale=1):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*scale
def qhp(t):return {"t":float(t),"charge":15+22.27046411874018*t,"hooke":1+0.3563655804274017*t,"power":5+t}
def zc(rows,key):
    out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        y1,y2=a[key],b[key]
        if y1*y2<0:
            t=a["t"]-y1*(b["t"]-a["t"])/(y2-y1)
            out.append({"low":a["setting"],"high":b["setting"],"t":float(t)})
    return out
def main():
    has60=all((ROOT/"out"/f"K31__{s['id']}_i60000.txt").is_file() for s in D["settings"])
    if has60:
        cps=D["standard"]["checkpoints"]+D["extended"]["additional_checkpoints"];late=D["extended"]["late_window"];track=D["extended"]["zero_track"];horizon=60000
    else:
        cps=D["standard"]["checkpoints"];late=D["standard"]["late_window"];track=D["standard"]["zero_track"];horizon=30000
    rows=[]
    for s in D["settings"]:
        vals=[]
        for it in cps:
            p=ROOT/"out"/f"K31__{s['id']}_i{it:05d}.txt"
            if not p.is_file():raise SystemExit(f"ERROR missing {p}")
            a=xyz(p);vals.append((it,length(a),rg(a)))
        L0,R0=vals[0][1],vals[0][2]
        E={it:0.5*((L/L0-1)+(R/R0-1)) for it,L,R in vals}
        lv=[E[i] for i in late];med=float(np.median(lv));dr=slope(late,lv,1000);span=float(max(lv)-min(lv))
        final=[E[late[-2]],E[late[-1]]]
        if abs(med)<=ET:cls="LATE_NEAR_ZERO"
        elif med>0 and min(final)>0:cls="LATE_EXPAND"
        elif med<0 and max(final)<0:cls="LATE_CONTRACT"
        else:cls="LATE_SIGN_INCONSISTENT"
        direct=abs(med)<=ET and abs(dr)<=DT and span<=ST
        r={"setting":s["id"],"t":s["t"],"charge":s["charge"],"hooke":s["hooke"],"power":s["power"],"role":s["role"],
           "early_E_per_100":slope(A["early_fit"],[E[i] for i in A["early_fit"]],100),
           "late_E_median":med,"late_drift_per_1000":dr,"late_span":span,"late_classification":cls,"direct_equilibrium":bool(direct)}
        for it in cps:r[f"E_i{it:05d}"]=E[it]
        rows.append(r)
    rows.sort(key=lambda r:r["t"])
    brackets=[]
    for a,b in zip(rows[:-1],rows[1:]):
        if {a["late_classification"],b["late_classification"]}=={"LATE_EXPAND","LATE_CONTRACT"}:
            y1,y2=a["late_E_median"],b["late_E_median"];t=a["t"]-y1*(b["t"]-a["t"])/(y2-y1)
            brackets.append({"low_setting":a["setting"],"high_setting":b["setting"],"interpolated":qhp(t)})
    track_rows=[]
    for it in track:
        xs=zc(rows,f"E_i{it:05d}")
        chosen=min(xs,key=lambda x:abs(x["t"]-1.260157177054118)) if xs else None
        track_rows.append({"iteration":it,"crossings":xs,"chosen":chosen,"chosen_qhp":qhp(chosen["t"]) if chosen else None})
    last=[x["chosen"]["t"] for x in track_rows[-3:] if x["chosen"]]
    spread=float(max(last)-min(last)) if len(last)>=2 else None
    converged=spread is not None and spread<=float(A["zero_track_t_spread_tolerance"])
    direct=[r for r in rows if r["direct_equilibrium"]]
    if direct:
        overall="DIRECT_LATE_EQUILIBRIUM_FOUND"
        best=min(direct,key=lambda r:abs(r["late_E_median"])/ET+abs(r["late_drift_per_1000"])/DT+r["late_span"]/ST)
        primary={"type":"direct","setting":best["setting"],"qhp":qhp(best["t"]),"late_E_median":best["late_E_median"],
                 "late_drift_per_1000":best["late_drift_per_1000"],"late_span":best["late_span"]}
    elif brackets and converged:
        overall="CONVERGED_LATE_ZERO_BRACKET_FOUND";primary={"type":"bracket",**brackets[0]}
    elif brackets:
        overall="LATE_ZERO_BRACKET_FOUND";primary={"type":"bracket",**brackets[0]}
    else:
        overall="NO_LATE_ZERO_IN_FROZEN_RANGE";primary=None
    old=json.loads((ROOT/"reference/Trefoil_Balance_Point_Campaign_v0.2.0_REPORT.json").read_text())
    olda=next(r for r in old["rows"] if r["setting"]=="R05");newa=next(r for r in rows if abs(r["t"]-1.25)<1e-12)
    anchor={"delta_E_i01000":newa["E_i01000"]-olda["E_i01000"],"delta_E_i10000":newa["E_i10000"]-olda["E_i10000"],
            "diagnostic_only":True}
    report={"format":"TREFOIL-QHP-LATE-ZERO-REPORT-2.1","horizon":horizon,"overall":overall,"primary_candidate":primary,
            "stable_late_brackets":brackets,"zero_track":track_rows,"zero_track_t_spread_last3":spread,
            "zero_track_converged":converged,"anchor_reproducibility":anchor,"rows":rows,
            "guardrail":"Geometric balance surrogate; not direct force proof."}
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    keys=["setting","t","charge","hooke","power","role","early_E_per_100","late_E_median","late_drift_per_1000","late_span","late_classification","direct_equilibrium"]+[f"E_i{i:05d}" for i in cps]
    with (ROOT/"analysis/runs.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for r in rows:w.writerow({k:r.get(k) for k in keys})
    md=["# Trefoil Balance Point Campaign v0.2.1","",f"**Horizon:** {horizon}",f"**Overall:** `{overall}`","",
        "## Primary candidate","",f"`{primary}`","","## Zero track","",
        "| iteration | t zero | q | h | p |","|---:|---:|---:|---:|---:|"]
    for x in track_rows:
        if x["chosen"]:
            q=x["chosen_qhp"];md.append(f"| {x['iteration']} | {q['t']:.9g} | {q['charge']:.9g} | {q['hooke']:.9g} | {q['power']:.9g} |")
        else:md.append(f"| {x['iteration']} | — | — | — | — |")
    md += ["",f"Last-three t spread: `{spread}`; converged: **{converged}**","",
           "## Long-time sweep","",
           "| setting | t | q | h | p | late median E | drift/1000 | span | class | direct eq |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for r in rows:
        md.append(f"| {r['setting']} | {r['t']:.3f} | {r['charge']:.6g} | {r['hooke']:.6g} | {r['power']:.6g} | {r['late_E_median']:.8g} | {r['late_drift_per_1000']:.8g} | {r['late_span']:.8g} | {r['late_classification']} | {r['direct_equilibrium']} |")
    md += ["","## Rule","",
           "A zero that keeps migrating with time is not accepted as a settled equilibrium.",
           "The 60k extension is run on all 20 settings, not selected candidates only."]
    (ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n")
    print("HORIZON:",horizon);print("OVERALL:",overall);print("PRIMARY:",json.dumps(primary,indent=2));print("ZERO TRACK SPREAD:",spread)
if __name__=="__main__":main()
