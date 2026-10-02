from __future__ import annotations
from pathlib import Path
import json,re

def val(v):
    if isinstance(v,str):return v
    if isinstance(v,bool):return "true" if v else "false"
    return f"{v:.15g}"

def metrics_block(run_id,it,save_coords,final_it):
    tag=f"i{it:06d}";o="__CAMPAIGN_REL__/out"
    lines=[
        f"echo CHECKPOINT {run_id} {it}/{final_it}",
        "centre","length","rog","safe","lnknum",
        f"data open {o}/{run_id}_{tag}.metrics.csv",
        'data format "/I,/l,/g,/N"',
        'data header "iteration,length,rog,nbeads"',
        "data","data close",
        f"save {o}/{run_id}_{tag}.k float",
    ]
    if save_coords=="all" or (save_coords=="final" and it==final_it):
        lines.append(f"coords {o}/{run_id}_{tag}.txt")
    return lines

def setup_prepared(run,baseline,fit_mindist):
    topo=run["topology"];state=run["qhp"]
    prepared=f"__CAMPAIGN_REL__/prepared_inputs/{topo['topo_id']}.txt"
    lines=["reset all",f"load {prepared}","mode cb","centre",
           f"fitto mindist {fit_mindist:.15g}","collision fast","energy model MD"]
    for k,v in baseline.items():lines.append(f"{k} = {val(v)}")
    lines += [f"charge = {val(state['q'])}",f"hooke = {val(state['h'])}",f"power = {val(state['p'])}"]
    return lines

def topology_probe_script(topo):
    """Export topology geometry for preparation.

    Single-component objects use one ordinary coords file.

    Multi-component objects are re-created once per component and `keep i`
    removes every other component before `coords`. This avoids relying on a
    particular KnotPlot build preserving blank-line component separators.
    """
    base="__CAMPAIGN_REL__/prep_raw"
    lines=["% AUTO-GENERATED topology bead-allocation probe"]
    ncomp=int(topo["components"])
    if ncomp==1:
        lines += ["reset all",topo["command"],
                  f"coords {base}/{topo['topo_id']}__comp000.txt"]
    else:
        for i in range(ncomp):
            lines += [
                "reset all",
                topo["command"],
                f"keep {i}",
                f"coords {base}/{topo['topo_id']}__comp{i:03d}.txt",
            ]
    lines.append("stop")
    return "\n".join(lines)+"\n"

def standard_script(run,baseline,checkpoints,fit_mindist,save_coords):
    rid=run["run_id"]
    lines=[
        "% AUTO-GENERATED MultiTopology QHP Sweep v0.3.1",
        f"% run_id={rid}",
        f"% topology={run['topology']['kind']}:{run['topology']['spec']}",
        f"% qhp={run['qhp']['q']:.15g},{run['qhp']['h']:.15g},{run['qhp']['p']:.15g}",
        *setup_prepared(run,baseline,fit_mindist),
        *metrics_block(rid,0,save_coords,checkpoints[-1])
    ]
    last=0
    for it in checkpoints[1:]:
        lines += [f"ago {it-last}",*metrics_block(rid,it,save_coords,checkpoints[-1])]
        last=it
    lines.append("stop")
    return "\n".join(lines)+"\n"

def resume_probe_script(run,baseline,from_it):
    """Load a checkpoint with no geometric transform and record its metrics."""
    state=run["qhp"];rid=run["run_id"]
    src=f"__CAMPAIGN_REL__/out/{rid}_i{from_it:06d}.k"
    o="__CAMPAIGN_REL__/resume_checks"
    tag=f"i{from_it:06d}"
    lines=[
        "% AUTO-GENERATED METRIC-NEUTRAL RESUME PROBE v0.3.2.3",
        f"% run_id={rid} resume_from={from_it}",
        "reset all",f"load {src}",
        "mode cb","collision fast","energy model MD",
    ]
    for k,v in baseline.items():lines.append(f"{k} = {val(v)}")
    lines += [
        f"charge = {val(state['q'])}",
        f"hooke = {val(state['h'])}",
        f"power = {val(state['p'])}",
        "length","rog","safe",
        f"data open {o}/{rid}_from_{tag}.metrics.csv",
        'data format "/I,/l,/g,/N"',
        'data header "iteration,length,rog,nbeads"',
        "data","data close","stop"
    ]
    return "\n".join(lines)+"\n"

def resume_script(run,baseline,remaining,from_it,fit_mindist,save_coords):
    state=run["qhp"];rid=run["run_id"]
    src=f"__CAMPAIGN_REL__/out/{rid}_i{from_it:06d}.k"
    # METRIC-NEUTRAL: no centre/refine/fitto after loading checkpoint.
    lines=[
        "% AUTO-GENERATED METRIC-NEUTRAL RESUME MultiTopology QHP Sweep v0.3.2.3",
        f"% run_id={rid} resume_from={from_it}",
        "reset all",f"load {src}",
        "mode cb","collision fast","energy model MD",
    ]
    for k,v in baseline.items():lines.append(f"{k} = {val(v)}")
    lines += [
        f"charge = {val(state['q'])}",
        f"hooke = {val(state['h'])}",
        f"power = {val(state['p'])}",
    ]
    last=from_it
    for it in remaining:
        lines += [f"ago {it-last}",*metrics_block(rid,it,save_coords,remaining[-1])]
        last=it
    lines.append("stop")
    return "\n".join(lines)+"\n"

def write_scripts(campaign,baseline,fit_mindist,save_coords):
    kd=campaign/"kpc";pd=campaign/"prep_kpc"
    kd.mkdir(parents=True,exist_ok=True);pd.mkdir(parents=True,exist_ok=True)
    plan=json.loads((campaign/"campaign.json").read_text())
    for topo in plan["topologies"]:
        (pd/f"{topo['topo_id']}.kpc").write_text(topology_probe_script(topo),encoding="utf-8",newline="\n")
    for r in plan["runs"]:
        (kd/f"{r['run_id']}.kpc").write_text(standard_script(r,baseline,plan["checkpoints"],fit_mindist,save_coords),encoding="utf-8",newline="\n")
    return len(plan["runs"])

def audit_scripts(campaign,baseline):
    runtime=set(baseline)|{"charge","hooke","power"}
    actions={"reset","load","torus","echo","mode","centre","fitto","collision","energy","length","rog","safe",
             "lnknum","data","save","coords","ago","stop"}
    bad=[];files=sorted((campaign/"kpc").glob("*.kpc"))
    for p in files:
        counts={"charge":0,"hooke":0,"power":0}
        for ln,raw in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
            s=raw.strip()
            if not s or s.startswith("%"):continue
            m=re.match(r"^([^=]+?)\s*=\s*(.+)$",s)
            if m:
                name=m.group(1).strip()
                if name not in runtime:bad.append((p.name,ln,f"unknown runtime variable {name}"))
                if name in counts:counts[name]+=1
                continue
            head=s.split()[0]
            if head not in actions:bad.append((p.name,ln,f"unknown command {head}"))
            if head in {"charge","hooke","power","timeincr","nbeads","alex"}:
                bad.append((p.name,ln,f"forbidden command-style parameter {head}"))
        for k,n in counts.items():
            if n!=1:bad.append((p.name,0,f"{k} assignment count {n}"))
    return files,bad
