from __future__ import annotations
from pathlib import Path
import json,csv,math

def _clean(v):
    if isinstance(v,float) and (math.isnan(v) or math.isinf(v)): return None
    if isinstance(v,dict): return {k:_clean(x) for k,x in v.items()}
    if isinstance(v,list): return [_clean(x) for x in v]
    return v

def write_reports(results,outdir):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    clean=_clean(results)
    for r in clean:
        (out/f"{r['id']}.json").write_text(json.dumps(r,indent=2),encoding='utf-8')
    summary={"suite":"SST Maxwell-Inspiration Falsifier","version":"0.1.0","results":clean}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (out/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['id','name','status','primary_metrics'])
        for r in clean:
            metrics='; '.join(f"{k}={v}" for k,v in r['metrics'].items() if isinstance(v,(int,float,str)) and v is not None)
            w.writerow([r['id'],r['name'],r['status'],metrics])
    return out/'summary.json'
