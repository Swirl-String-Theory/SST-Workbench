from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .stress import run_stress
from .reduced_momentum import run_reduced_momentum
from .storage import run_storage
from .blind import unblind_report


def _load_cfg(path: Path): return json.loads(path.read_text(encoding="utf-8"))

def main(argv=None):
    p=argparse.ArgumentParser(prog="sst-maxwell-blind")
    sub=p.add_subparsers(dest="cmd",required=True)
    r=sub.add_parser("run",help="run target-blind preregistered analysis")
    r.add_argument("--config",type=Path,default=Path("config/preregister.json")); r.add_argument("--campaign",type=Path); r.add_argument("--reduced-momentum",type=Path); r.add_argument("--storage",type=Path); r.add_argument("--outdir",type=Path,default=Path("results_blind")); r.add_argument("--allow-missing-required",action="store_true")
    u=sub.add_parser("unblind",help="verify commitments and compare frozen blind outputs with committed targets")
    u.add_argument("--blind-report",type=Path,required=True); u.add_argument("--commitments",type=Path,default=Path("blind/commitments.json")); u.add_argument("--key",type=Path,required=True); u.add_argument("--out",type=Path,default=Path("results_unblinded.json"))
    a=p.parse_args(argv)
    if a.cmd=="unblind":
        out=unblind_report(a.blind_report,a.commitments,a.key,a.out); print(json.dumps(out,indent=2)); return 0
    cfg=_load_cfg(a.config); a.outdir.mkdir(parents=True,exist_ok=True); tracks={}; missing=[]
    if a.campaign: tracks["stress"]=run_stress(a.campaign,a.outdir,cfg["stress_track"],cfg["blindness"]["split_seed"])
    elif cfg["stress_track"]["required"]: missing.append("stress")
    if a.reduced_momentum: tracks["reduced_momentum"]=run_reduced_momentum(a.reduced_momentum,a.outdir,cfg["reduced_momentum_track"],cfg["blindness"])
    elif cfg["reduced_momentum_track"]["required"]: missing.append("reduced_momentum")
    if a.storage: tracks["storage_current"]=run_storage(a.storage,a.outdir,cfg["storage_current_track"])
    elif cfg["storage_current_track"]["required"]: missing.append("storage_current")
    statuses=[v["status"] for v in tracks.values()]
    if missing and not a.allow_missing_required: overall="INCONCLUSIVE"
    elif "FAIL" in statuses: overall="FAIL"
    elif "INCONCLUSIVE" in statuses: overall="INCONCLUSIVE"
    else: overall="PASS" if statuses else "INCONCLUSIVE"
    report={"protocol_version":cfg["protocol_version"],"blindness":cfg["blindness"],"overall_status":overall,"missing_required_tracks":missing,"tracks":tracks,"decision_rule":cfg["decision_rule"]}
    out=a.outdir/"blind_report.json"; out.write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report,indent=2)); return 1 if overall=="FAIL" else 0

if __name__=="__main__": raise SystemExit(main())
