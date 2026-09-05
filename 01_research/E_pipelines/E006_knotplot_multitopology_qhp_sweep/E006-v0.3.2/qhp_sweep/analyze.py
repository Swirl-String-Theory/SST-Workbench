from __future__ import annotations
from pathlib import Path
import csv,json,math
import numpy as np

def metric(campaign,rid,it):
    p=campaign/"out"/f"{rid}_i{it:06d}.metrics.csv"
    if not p.is_file():return None
    rows=[x.strip() for x in p.read_text(encoding="utf-8",errors="ignore").splitlines() if x.strip()]
    if len(rows)<2:return None
    vals=rows[-1].split(",")
    if len(vals)<5:return None
    try:return {"iteration":int(float(vals[0])),"length":float(vals[1]),"rog":float(vals[2]),
                "nbeads":int(float(vals[3])),"safeness":float(vals[4])}
    except Exception:return None

def slope(xs,ys,scale=1.0):
    x=np.asarray(xs,float);y=np.asarray(ys,float)
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*scale

def analyze(campaign):
    plan=json.loads((campaign/"campaign.json").read_text())
    cps=plan["checkpoints"]; rows=[]
    for r in plan["runs"]:
        rid=r["run_id"];ms=[metric(campaign,rid,it) for it in cps]
        if any(x is None for x in ms):
            rows.append({"run_id":rid,"topology_id":r["topology"]["topo_id"],"complete":False})
            continue
        L0,R0=ms[0]["length"],ms[0]["rog"]
        E=[0.5*((m["length"]/L0-1)+(m["rog"]/R0-1)) for m in ms]
        early_idx=[i for i,it in enumerate(cps) if it<=100]
        late_idx=list(range(max(0,len(cps)-4),len(cps)))
        le=[E[i] for i in late_idx]; li=[cps[i] for i in late_idx]
        med=float(np.median(le));dr=slope(li,le,1000.0);span=float(max(le)-min(le))
        tol=plan["analysis_tolerances"]
        direct=abs(med)<=tol["late_E_abs"] and abs(dr)<=tol["late_drift_per_1000"] and span<=tol["late_span"]
        rec={
            "run_id":rid,"topology_id":r["topology"]["topo_id"],"topology_kind":r["topology"]["kind"],
            "topology_spec":r["topology"]["spec"],"components":r["topology"]["components"],
            "qhp_index":r["qhp"]["index"],"q":r["qhp"]["q"],"h":r["qhp"]["h"],"p":r["qhp"]["p"],
            "line_alpha":r["qhp"].get("line_alpha"),"grid_index":r["qhp"].get("grid_index"),
            "complete":True,"early_E_per_100":slope([cps[i] for i in early_idx],[E[i] for i in early_idx],100.0),
            "late_E_median":med,"late_drift_per_1000":dr,"late_span":span,
            "final_E":E[-1],"min_safeness":min(m["safeness"] for m in ms),
            "direct_equilibrium":bool(direct),
        }
        rows.append(rec)

    complete=[r for r in rows if r.get("complete")]
    bytop={}
    for r in complete:bytop.setdefault(r["topology_id"],[]).append(r)
    summaries=[]
    for tid,rr in sorted(bytop.items()):
        rr.sort(key=lambda x:x["qhp_index"])
        best=min(rr,key=lambda x:(abs(x["late_E_median"]),abs(x["late_drift_per_1000"])))
        crossings=[]
        if plan["qhp_mode"]=="line":
            for a,b in zip(rr[:-1],rr[1:]):
                y1,y2=a["late_E_median"],b["late_E_median"]
                if y1*y2<0:
                    f=-y1/(y2-y1)
                    crossings.append({
                        "low":a["run_id"],"high":b["run_id"],
                        "q":a["q"]+f*(b["q"]-a["q"]),
                        "h":a["h"]+f*(b["h"]-a["h"]),
                        "p":a["p"]+f*(b["p"]-a["p"]),
                        "fraction":float(f)
                    })
        direct=[r["run_id"] for r in rr if r["direct_equilibrium"]]
        summaries.append({
            "topology_id":tid,"kind":rr[0]["topology_kind"],"spec":rr[0]["topology_spec"],
            "n_complete":len(rr),"best_run":best["run_id"],
            "best_qhp":[best["q"],best["h"],best["p"]],
            "best_late_E_median":best["late_E_median"],
            "best_late_drift_per_1000":best["late_drift_per_1000"],
            "direct_equilibria":direct,"line_zero_crossings":crossings,
        })

    ad=campaign/"analysis";ad.mkdir(exist_ok=True)
    (ad/"REPORT.json").write_text(json.dumps({"campaign":plan,"summaries":summaries,"rows":rows},indent=2)+"\n",encoding="utf-8")
    if rows:
        cols=sorted(set().union(*(r.keys() for r in rows)))
        with (ad/"runs.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            for r in rows:
                q=dict(r)
                if isinstance(q.get("grid_index"),list):q["grid_index"]=".".join(map(str,q["grid_index"]))
                w.writerow(q)
    md=["# MultiTopology QHP Sweep Report","",
        f"- QHP mode: **{plan['qhp_mode']}**",
        f"- Topologies: **{len(plan['topologies'])}**",
        f"- QHP states/topology: **{len(plan['qhp_states'])}**",
        f"- Planned runs: **{len(plan['runs'])}**",
        f"- Max ago: **{plan['max_ago']}**","",
        "| topology | kind | best q | best h | best p | late E | drift/1000 | direct eq | zero crossings |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in summaries:
        q,h,p=s["best_qhp"]
        md.append(f"| {s['spec']} | {s['kind']} | {q:.8g} | {h:.8g} | {p:.8g} | {s['best_late_E_median']:.8g} | {s['best_late_drift_per_1000']:.8g} | {len(s['direct_equilibria'])} | {len(s['line_zero_crossings'])} |")
    md += ["","## Interpretation guardrail","",
           "The sweep searches for a geometric expansion/contraction balance in KnotPlot dynamics.",
           "A near-zero E state is not by itself proof of a mechanical restoring equilibrium or TBK/RPO stability."]
    (ad/"REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print(f"ANALYSIS PASS: complete={len(complete)}/{len(rows)} topologies={len(summaries)}")
    for s in summaries:
        print(s["spec"],"best",s["best_qhp"],"lateE",s["best_late_E_median"],"crossings",len(s["line_zero_crossings"]))
    return 0
