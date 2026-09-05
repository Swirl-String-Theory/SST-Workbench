from pathlib import Path
import argparse,json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def status():
    required=[0,200000]+[int(x) for x in D["continuation"]["checkpoints"]]
    rows=[]
    missing_total=[]
    for s in D["panel"]:
        rid=f"XQHP__{s['id']}"
        present=[]
        missing=[]
        for it in required:
            p=ROOT/"out"/f"{rid}_i{it:06d}.txt"
            if p.is_file() and p.stat().st_size>0:
                present.append(it)
            else:
                missing.append(it)
                missing_total.append(str(p))
        latest=max(present) if present else None
        rows.append({
            "id":s["id"],"t":s["t"],"role":s["role"],
            "present":present,"missing":missing,"latest_present":latest,
            "complete":not missing,
        })
    payload={
        "format":"TREFOIL-V0242-CONTINUATION-COMPLETENESS-1.0",
        "overall":"PASS" if not missing_total else "INCOMPLETE",
        "required_iterations":required,
        "complete_settings":sum(1 for x in rows if x["complete"]),
        "total_settings":len(rows),
        "missing_file_count":len(missing_total),
        "rows":rows,
    }
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/CONTINUATION_COMPLETENESS.json").write_text(
        json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    return payload

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--require-complete",action="store_true")
    a=ap.parse_args()
    p=status()
    print("CONTINUATION COMPLETENESS:",p["overall"])
    print("settings:",p["complete_settings"],"/",p["total_settings"],"complete")
    for x in p["rows"]:
        if not x["complete"]:
            print(f"  {x['id']} t={x['t']}: latest={x['latest_present']} missing={x['missing']}")
    if a.require_complete and p["overall"]!="PASS":
        print("")
        print("Recovery command:")
        print("  run_resume_continuation_then_analyze.cmd")
        return 6
    return 0
if __name__=="__main__":raise SystemExit(main())
