from pathlib import Path
import argparse,json,re
BROKEN=("unknown data field","no data format set","0 data records written")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--campaign",required=True);a=ap.parse_args()
    root=Path(a.campaign).resolve()
    C=json.loads((root/"campaign.json").read_text(encoding="utf-8"))
    cps=[int(x) for x in C["checkpoints"]]
    badlogs=[]
    for p in sorted((root/"logs").glob("*.log")):
        t=p.read_text(encoding="utf-8",errors="replace").lower()
        hits=[x for x in BROKEN if x in t]
        if hits:badlogs.append({"log":p.name,"hits":hits})
    missing=[]
    for run in C["runs"]:
        for it in cps:
            p=root/"out"/f"{run['run_id']}_i{it:06d}.k"
            if not p.is_file() or p.stat().st_size==0:missing.append(str(p))
    empties=[str(p) for p in (root/"out").glob("*.metrics.csv") if p.stat().st_size==0]
    status="DYNAMICS_STATES_COMPLETE_METRICS_EXPORT_BROKEN" if not missing and badlogs else ("PASS" if not missing and not badlogs else "FAIL")
    payload={"format":"KNOTPLOT-QHP-INTEGRITY-AUDIT-3.2.4","status":status,
             "expected_states":len(C["runs"])*len(cps),"missing_states":missing,
             "broken_metric_logs":badlogs,"empty_metrics_csv":empties}
    (root/"analysis_recovered").mkdir(exist_ok=True)
    (root/"analysis_recovered/INTEGRITY_AUDIT.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("STATUS:",status)
    print("missing states:",len(missing))
    print("broken metric logs:",len(badlogs))
    print("empty metrics csv:",len(empties))
    # Existing broken metrics is recoverable and therefore not process-fatal if states are complete.
    return 1 if missing else 0
if __name__=="__main__":raise SystemExit(main())
