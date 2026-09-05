from pathlib import Path
import json, collections

ROOT=Path(__file__).resolve().parent
for stage in ("probe","extended"):
    audits=[]
    for p in sorted((ROOT/"logs"/stage).glob("*_audit.json")):
        try:
            a=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if a.get("status")=="RUN_FAILED":
            audits.append(a)
    if not audits:
        continue
    print(f"[{stage.upper()}] RUN_FAILED candidates: {len(audits)}")
    fam=collections.Counter(a.get("family","?") for a in audits)
    print("  families:",dict(fam))
    for a in audits:
        print(f"  - {a.get('candidate')}: exit={a.get('process_exit')} loaded_line={a.get('loaded_line')}")
        for e in a.get("hard_errors",[])[:3]:
            print("      hard:",e.get("text",e))
        for m in a.get("missing_outputs",[])[:3]:
            print("      missing:",m)
