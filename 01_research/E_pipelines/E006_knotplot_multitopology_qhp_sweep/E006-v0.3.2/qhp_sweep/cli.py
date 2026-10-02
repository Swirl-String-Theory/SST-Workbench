from __future__ import annotations
import argparse,json,os,shutil,sys
from pathlib import Path
from .model import *
from .kpc import write_scripts,audit_scripts
from .runner import execute
from .analyze import analyze

PACKAGE=Path(__file__).resolve().parents[1]
BASELINE=json.loads((PACKAGE/"reference/frozen_non_qhp_baseline.json").read_text())

def parser():
    p=argparse.ArgumentParser(
      description="KnotPlot multi-topology q/h/p sweep with checkpoint/resume support",
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--qhp-min",required=True,help="q,h,p lower tuple, e.g. 42.05,1.433,6.215")
    p.add_argument("--qhp-max",required=True,help="q,h,p upper tuple")
    p.add_argument("--qhp-mode",choices=["line","grid"],default="line",
                   help="line interpolates q/h/p together; grid takes Cartesian product")
    p.add_argument("--scripts",type=int,default=20,
                   help="number of q/h/p scripts per topology in line mode")
    p.add_argument("--qhp-points",type=int,default=None,
                   help="backwards-compatible alias for --scripts; do not set both to different values")
    p.add_argument("--qhp-steps",default="5,5,5",help="q,h,p grid counts in grid mode")
    p.add_argument("--max-ago",type=int,default=100000)
    p.add_argument("--checkpoints",default="auto",help="auto or comma-separated absolute iteration numbers")
    p.add_argument("--knots",default="",help="comma list, e.g. 3.1,5.1,7.1")
    p.add_argument("--links",default="",help="comma list, e.g. 6.3.3,6.3.1")
    p.add_argument("--torus",default="",help="comma list p.q, e.g. 3.3,3.6,6.9")
    p.add_argument("--beads-per-component",type=int,default=300,
                   help="total bead budget = component_count * this value; then distributed by measured component length")
    p.add_argument("--min-beads-per-component",type=int,default=12,
                   help="minimum reserved beads for each component before proportional allocation")
    p.add_argument("--total-beads",type=int,default=None,
                   help="override automatic per-component sizing for every topology")
    p.add_argument("--fit-mindist",type=float,default=1.05)
    p.add_argument("--save-coords",choices=["none","final","all"],default="final")
    p.add_argument("--name",default=None,help="campaign folder name; default is deterministic hash")
    p.add_argument("--max-runs",type=int,default=5000,help="hard accidental-explosion guard")
    p.add_argument("--generate-only",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--force",action="store_true",help="ignore checkpoint resume and restart each run")
    p.add_argument("--run-limit",type=int,default=None,help="debug: execute only first N planned runs")
    p.add_argument("--progress-every",type=int,default=30,help="seconds between live timer/ETA heartbeats")
    p.add_argument("--late-E-tol",type=float,default=3e-4)
    p.add_argument("--late-drift-tol",type=float,default=7.5e-5)
    p.add_argument("--late-span-tol",type=float,default=6e-4)
    return p

def build(a):
    qmin=parse_triplet(a.qhp_min,"--qhp-min");qmax=parse_triplet(a.qhp_max,"--qhp-max")
    steps=parse_steps(a.qhp_steps)
    tops=topology_list(a.knots,a.links,a.torus,a.beads_per_component,a.total_beads)
    points=a.scripts
    if a.qhp_points is not None:
        if a.scripts!=20 and a.qhp_points!=a.scripts:
            raise ValueError("--scripts and --qhp-points disagree")
        points=a.qhp_points
    states=qhp_states(qmin,qmax,a.qhp_mode,points,steps)
    cps=parse_checkpoints(a.checkpoints,a.max_ago)
    n=len(tops)*len(states)
    if n>a.max_runs:raise ValueError(f"Planned {n} runs exceeds --max-runs={a.max_runs}. Raise --max-runs explicitly if intentional.")
    seed={
      "version":"0.3.0","qhp_min":qmin,"qhp_max":qmax,"qhp_mode":a.qhp_mode,
      "scripts":points,"qhp_points":points,"qhp_steps":steps,"max_ago":a.max_ago,
      "checkpoints":cps,"topologies":[asdict(t) for t in tops],
      "beads_per_component":a.beads_per_component,"total_beads":a.total_beads,
      "fit_mindist":a.fit_mindist,"save_coords":a.save_coords,
    }
    name=a.name or f"campaign_{campaign_hash(seed)}"
    if not re.match(r"^[A-Za-z0-9_.-]+$",name):raise ValueError("--name may contain only A-Z a-z 0-9 _ . -")
    campaign=PACKAGE/"campaigns"/name
    runs=[]
    for t in tops:
        td=asdict(t)
        for s in states:
            rid=f"{t.topo_id}__QHP_{s['index']:04d}"
            runs.append({"run_id":rid,"topology":td,"qhp":s})
    plan={
      "format":"KNOTPLOT-MULTITOPOLOGY-QHP-SWEEP-3.0",
      "name":name,"campaign_dir":str(campaign),"qhp_min":qmin,"qhp_max":qmax,
      "qhp_mode":a.qhp_mode,"scripts":points,"qhp_points":points,"qhp_steps":steps,
      "max_ago":a.max_ago,"checkpoints":cps,"topologies":[asdict(t) for t in tops],
      "qhp_states":states,"runs":runs,"beads_per_component":a.beads_per_component,
      "total_beads":a.total_beads,"min_beads_per_component":a.min_beads_per_component,"fit_mindist":a.fit_mindist,"save_coords":a.save_coords,"progress_every":a.progress_every,
      "analysis_tolerances":{"late_E_abs":a.late_E_tol,"late_drift_per_1000":a.late_drift_tol,"late_span":a.late_span_tol},
      "baseline_sha256":__import__("hashlib").sha256((PACKAGE/"reference/frozen_non_qhp_baseline.json").read_bytes()).hexdigest()
    }
    return campaign,plan

def main(argv=None):
    p=parser()
    if argv is None and len(sys.argv)==1:
        p.print_help();return 2
    a=p.parse_args(argv)
    try:campaign,plan=build(a)
    except Exception as e:
        print("CONFIG ERROR:",e,file=sys.stderr);return 2

    print("="*72)
    print("KnotPlot MultiTopology QHP Sweep v0.3.2.3")
    print("="*72)
    print("Campaign :",plan["name"])
    print("Mode     :",plan["qhp_mode"])
    print("QHP      :",plan["qhp_min"],"->",plan["qhp_max"])
    print("Scripts  :",len(plan["qhp_states"]),"per topology")
    print("Topology :",len(plan["topologies"]))
    print("Runs     :",len(plan["runs"]))
    print("Max ago  :",plan["max_ago"])
    print("Checkpts :",plan["checkpoints"])
    for t in plan["topologies"]:
        print(f"  {t['kind']:5s} {t['spec']:8s} components={t['components']} beads={t['nbeads']} command={t['command']}")
    if a.dry_run:return 0

    campaign.mkdir(parents=True,exist_ok=True)
    (campaign/"campaign.json").write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
    for x in ("out","logs","analysis","runtime_kpc"): (campaign/x).mkdir(exist_ok=True)
    n=write_scripts(campaign,BASELINE,a.fit_mindist,a.save_coords)
    files,bad=audit_scripts(campaign,BASELINE)
    if bad:
        print("KPC AUDIT FAIL",file=sys.stderr)
        for x in bad[:100]:print(x,file=sys.stderr)
        return 3
    print(f"KPC AUDIT PASS: {len(files)}/{len(files)}")
    if a.generate_only:
        print("GENERATE ONLY:",campaign);return 0

    rc=execute(PACKAGE,campaign,BASELINE,a.fit_mindist,a.save_coords,a.force,a.run_limit,a.progress_every)
    if rc:return rc
    return analyze(campaign)

if __name__=="__main__":raise SystemExit(main())
