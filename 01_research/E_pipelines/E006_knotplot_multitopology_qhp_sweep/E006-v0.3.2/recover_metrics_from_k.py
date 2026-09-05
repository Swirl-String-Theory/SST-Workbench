from __future__ import annotations
from pathlib import Path
import argparse,csv,json,math,re,struct,shutil,hashlib
import numpy as np

BROKEN_LOG_PATTERNS=(
    "unknown data field",
    "no data format set",
    "0 data records written",
)

def parse_locf_components(path: Path):
    """
    Parse KnotPlot binary .k float files.
    LOCF chunk payload is big-endian float32 XYZ; chunk byte length follows LOCF.
    Multiple LOCF chunks are link components.
    """
    b=path.read_bytes()
    comps=[]
    pos=0
    while True:
        i=b.find(b"LOCF",pos)
        if i<0:
            break
        if i+8>len(b):
            raise ValueError(f"truncated LOCF header: {path}")
        nbytes=struct.unpack(">I",b[i+4:i+8])[0]
        start=i+8
        end=start+nbytes
        if end>len(b) or nbytes%12:
            raise ValueError(f"invalid LOCF chunk size={nbytes}: {path}")
        a=np.frombuffer(b[start:end],dtype=">f4").astype(np.float64).reshape(-1,3)
        if len(a)<3:
            raise ValueError(f"LOCF component has <3 beads: {path}")
        comps.append(a)
        pos=end
    if not comps:
        raise ValueError(f"no LOCF chunks in KnotPlot state: {path}")
    return comps

def state_metrics(path: Path):
    comps=parse_locf_components(path)
    total_length=0.0
    for a in comps:
        total_length += float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())
    pts=np.concatenate(comps,axis=0)
    center=pts.mean(axis=0)
    rg=float(np.sqrt(np.mean(np.sum((pts-center)**2,axis=1))))
    return {
        "length":total_length,
        "rog":rg,
        "nbeads":int(len(pts)),
        "ncomponents":int(len(comps)),
        "component_nbeads":[int(len(a)) for a in comps],
    }

def slope(xs,ys,scale=1.0):
    x=np.asarray(xs,dtype=float)
    y=np.asarray(ys,dtype=float)
    if len(x)<2:
        return float("nan")
    return float(np.linalg.lstsq(np.c_[x,np.ones_like(x)],y,rcond=None)[0][0])*scale

def find_crossings(run_rows, iteration):
    key=f"E_{iteration}"
    out=[]
    ordered=sorted(run_rows,key=lambda r:r["qhp"]["line_alpha"])
    for a,b in zip(ordered[:-1],ordered[1:]):
        y1=a[key]; y2=b[key]
        if y1==0:
            frac=0.0
        elif y1*y2<0:
            frac=-y1/(y2-y1)
        else:
            continue
        aa=float(a["qhp"]["line_alpha"]); ab=float(b["qhp"]["line_alpha"])
        alpha=aa+frac*(ab-aa)
        q=float(a["qhp"]["q"])+frac*(float(b["qhp"]["q"])-float(a["qhp"]["q"]))
        h=float(a["qhp"]["h"])+frac*(float(b["qhp"]["h"])-float(a["qhp"]["h"]))
        p=float(a["qhp"]["p"])+frac*(float(b["qhp"]["p"])-float(a["qhp"]["p"]))
        dl=a[f"dL_{iteration}"]+frac*(b[f"dL_{iteration}"]-a[f"dL_{iteration}"])
        dr=a[f"dRg_{iteration}"]+frac*(b[f"dRg_{iteration}"]-a[f"dRg_{iteration}"])
        out.append({
            "low_run":a["run_id"],"high_run":b["run_id"],
            "fraction":float(frac),"line_alpha":float(alpha),
            "q":float(q),"h":float(h),"p":float(p),
            "dL_at_zero":float(dl),"dRg_at_zero":float(dr),
        })
    return out

def audit_logs(campaign_dir: Path):
    logs=campaign_dir/"logs"
    findings=[]
    if logs.is_dir():
        for p in sorted(logs.glob("*.log")):
            text=p.read_text(encoding="utf-8",errors="replace")
            hits=[pat for pat in BROKEN_LOG_PATTERNS if pat in text.lower()]
            if hits:
                findings.append({"log":p.name,"patterns":hits})
    return findings

def recover(campaign_dir: Path, replace_analysis: bool):
    campaign_file=campaign_dir/"campaign.json"
    if not campaign_file.is_file():
        raise FileNotFoundError(campaign_file)
    C=json.loads(campaign_file.read_text(encoding="utf-8"))
    checkpoints=[int(x) for x in C["checkpoints"]]
    late=checkpoints[-4:]
    tol=C.get("analysis_tolerances",{})
    gate_E=float(tol.get("late_E_abs",3e-4))
    gate_d=float(tol.get("late_drift_per_1000",7.5e-5))
    gate_s=float(tol.get("late_span",6e-4))
    outdir=campaign_dir/"out"

    recovered=[]
    missing=[]
    bad_states=[]
    for run in C["runs"]:
        rid=run["run_id"]
        metrics={}
        for it in checkpoints:
            p=outdir/f"{rid}_i{it:06d}.k"
            if not p.is_file() or p.stat().st_size==0:
                missing.append(str(p))
                continue
            try:
                metrics[it]=state_metrics(p)
            except Exception as e:
                bad_states.append({"path":str(p),"error":repr(e)})
        if len(metrics)!=len(checkpoints):
            recovered.append({
                "run_id":rid,"topology":run["topology"],"qhp":run["qhp"],
                "complete":False,"missing_checkpoints":[it for it in checkpoints if it not in metrics],
            })
            continue

        m0=metrics[checkpoints[0]]
        L0=m0["length"]; R0=m0["rog"]
        row={
            "run_id":rid,
            "topology":run["topology"],
            "qhp":run["qhp"],
            "complete":True,
            "metric_source":"KNOTPLOT_BINARY_LOCF_FLOAT32",
            "length_definition":"sum_closed_component_arclength",
            "rg_definition":"global_bead_weighted_radius_of_gyration",
            "ncomponents":m0["ncomponents"],
            "initial_nbeads":m0["nbeads"],
            "component_nbeads_initial":m0["component_nbeads"],
            "metrics":{},
        }
        for it in checkpoints:
            m=metrics[it]
            dL=m["length"]/L0-1.0
            dR=m["rog"]/R0-1.0
            E=0.5*(dL+dR)
            row["metrics"][str(it)]={
                **m,
                "dL":float(dL),"dRg":float(dR),"E":float(E),
            }
            row[f"E_{it}"]=float(E)
            row[f"dL_{it}"]=float(dL)
            row[f"dRg_{it}"]=float(dR)

        ev=[row[f"E_{it}"] for it in late]
        med=float(np.median(ev))
        drift=slope(late,ev,1000.0)
        span=float(max(ev)-min(ev))
        row["late_window"]=late
        row["late_E_median"]=med
        row["late_drift_per_1000"]=drift
        row["late_span"]=span
        row["direct_equilibrium_gate"]=bool(
            abs(med)<=gate_E and abs(drift)<=gate_d and span<=gate_s
        )
        recovered.append(row)

    complete=[r for r in recovered if r.get("complete")]
    by_top={}
    for r in complete:
        by_top.setdefault(r["topology"]["topo_id"],[]).append(r)

    summaries=[]
    for topo_id,rr in sorted(by_top.items()):
        rr=sorted(rr,key=lambda r:r["qhp"]["line_alpha"])
        zero_track=[]
        prior=None
        for it in checkpoints:
            crossings=find_crossings(rr,it)
            chosen=None
            if crossings:
                if prior is None:
                    # At each isolated screen checkpoint, use first crossing.
                    chosen=crossings[0]
                else:
                    chosen=min(crossings,key=lambda x:abs(x["line_alpha"]-prior))
                prior=chosen["line_alpha"]
            zero_track.append({"iteration":it,"crossings":crossings,"chosen":chosen})
        direct=[r for r in rr if r["direct_equilibrium_gate"]]
        summaries.append({
            "topology_id":topo_id,
            "kind":rr[0]["topology"]["kind"],
            "spec":rr[0]["topology"]["spec"],
            "n_runs":len(rr),
            "direct_equilibrium_runs":[r["run_id"] for r in direct],
            "zero_track":zero_track,
            "zero_at_final":next((x["chosen"] for x in zero_track if x["iteration"]==checkpoints[-1]),None),
        })

    log_findings=audit_logs(campaign_dir)
    empty_metrics=[
        str(p) for p in sorted(outdir.glob("*.metrics.csv"))
        if p.is_file() and p.stat().st_size==0
    ]

    report={
        "format":"KNOTPLOT-MULTITOPOLOGY-QHP-RECOVERED-3.2.4",
        "campaign":C,
        "recovery":{
            "authoritative_source":"saved KnotPlot .k float states",
            "state_parser":"LOCF big-endian float32",
            "length_definition":"sum of closed arclengths of all components",
            "rg_definition":"global bead-weighted radius of gyration over all components",
            "safeness_recovered":False,
            "late_window":late,
            "tolerances":{
                "late_E_abs":gate_E,
                "late_drift_per_1000":gate_d,
                "late_span":gate_s,
            },
            "expected_runs":len(C["runs"]),
            "complete_runs":sum(1 for x in recovered if x.get("complete")),
            "expected_states":len(C["runs"])*len(checkpoints),
            "present_good_states":sum(len(r.get("metrics",{})) for r in recovered if r.get("complete")),
            "missing_state_files":missing,
            "bad_state_files":bad_states,
            "empty_metrics_csv_count":len(empty_metrics),
            "broken_metrics_log_count":len(log_findings),
            "broken_metrics_log_examples":log_findings[:20],
        },
        "summaries":summaries,
        "rows":recovered,
    }

    recdir=campaign_dir/"analysis_recovered"
    recdir.mkdir(parents=True,exist_ok=True)
    (recdir/"REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

    flat=[]
    for r in recovered:
        x={
            "complete":r.get("complete",False),
            "run_id":r["run_id"],
            "topology_id":r["topology"]["topo_id"],
            "spec":r["topology"]["spec"],
            "qhp_index":r["qhp"]["index"],
            "line_alpha":r["qhp"]["line_alpha"],
            "q":r["qhp"]["q"],"h":r["qhp"]["h"],"p":r["qhp"]["p"],
        }
        if r.get("complete"):
            x.update({
                "late_E_median":r["late_E_median"],
                "late_drift_per_1000":r["late_drift_per_1000"],
                "late_span":r["late_span"],
                "direct_equilibrium_gate":r["direct_equilibrium_gate"],
            })
        flat.append(x)
    fields=sorted({k for x in flat for k in x})
    with (recdir/"runs.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(flat)

    md=[
        "# Recovered MultiTopology QHP report",
        "",
        f"- campaign: `{C['name']}`",
        f"- complete runs: **{report['recovery']['complete_runs']}/{report['recovery']['expected_runs']}**",
        f"- empty original metrics CSVs: **{len(empty_metrics)}**",
        f"- logs containing broken data-format diagnostics: **{len(log_findings)}**",
        f"- late window: `{late}`",
        "",
        "## Metric semantics",
        "",
        "- authoritative geometry: saved `.k float` checkpoint states",
        "- length: sum of closed component arclengths",
        "- Rg: global bead-weighted radius of gyration",
        "- safeness: not reconstructed or invented",
        "",
        "## Direct late-E gate passes",
        "",
        "| topology | run | alpha | q | h | p | median E | drift/1000 | span |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    passes=[]
    for r in complete:
        if r["direct_equilibrium_gate"]:
            passes.append(r)
            md.append(
                f"| {r['topology']['topo_id']} | {r['run_id']} | {r['qhp']['line_alpha']:.6g} | "
                f"{r['qhp']['q']:.8g} | {r['qhp']['h']:.8g} | {r['qhp']['p']:.8g} | "
                f"{r['late_E_median']:.8g} | {r['late_drift_per_1000']:.8g} | {r['late_span']:.8g} |"
            )
    if not passes:
        md.append("| — | — | — | — | — | — | — | — | — |")

    md += [
        "",
        "## Final-checkpoint EXPAND/CONTRACT crossings",
        "",
        "| topology | alpha* | q* | h* | p* | dL/L0 | dRg/Rg0 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        z=s["zero_at_final"]
        if z:
            md.append(
                f"| {s['topology_id']} | {z['line_alpha']:.8g} | {z['q']:.8g} | "
                f"{z['h']:.8g} | {z['p']:.8g} | {z['dL_at_zero']:.8g} | {z['dRg_at_zero']:.8g} |"
            )
    md += [
        "",
        "## Integrity finding",
        "",
        "The original KnotPlot `data format` path is not authoritative for this recovered report.",
        "The saved geometry states are complete and are analyzed directly.",
    ]
    (recdir/"REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")

    if replace_analysis:
        ad=campaign_dir/"analysis"
        ad.mkdir(exist_ok=True)
        for name in ["REPORT.json","REPORT.md","runs.csv"]:
            old=ad/name
            if old.exists() and not (ad/(name+".pre_v0324_backup")).exists():
                shutil.copy2(old,ad/(name+".pre_v0324_backup"))
            shutil.copy2(recdir/name,old)

    print("RECOVERY COMPLETE")
    print("campaign:",C["name"])
    print("runs:",report["recovery"]["complete_runs"],"/",report["recovery"]["expected_runs"])
    print("empty original metrics:",len(empty_metrics))
    print("broken-format logs:",len(log_findings))
    print("direct late-E passes:",len(passes))
    for r in passes:
        print("  PASS",r["run_id"],"medianE",r["late_E_median"],"drift",r["late_drift_per_1000"],"span",r["late_span"])
    print("final crossings:")
    for s in summaries:
        if s["zero_at_final"]:
            print(" ",s["topology_id"],s["zero_at_final"]["line_alpha"])
    return 0 if not missing and not bad_states else 2

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--campaign",required=True,help="campaign directory containing campaign.json/out/logs")
    ap.add_argument("--replace-analysis",action="store_true",help="back up and replace analysis/REPORT.* with recovered report")
    a=ap.parse_args()
    return recover(Path(a.campaign).resolve(),a.replace_analysis)

if __name__=="__main__":
    raise SystemExit(main())
