from __future__ import annotations
from pathlib import Path
import csv, json, math
from . import __version__, WORKBENCH_PREFIX

def clean(v):
    if isinstance(v,float) and (math.isnan(v) or math.isinf(v)): return None
    if isinstance(v,dict): return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [clean(x) for x in v]
    return v

def write_test_reports(results,outdir,meta=None):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True); c=clean(results)
    for r in c: (out/f"{r['id']}.json").write_text(json.dumps(r,indent=2),encoding='utf-8')
    summary={"suite":"4_SST Maxwell-Inspiration Falsifier","version":__version__,"prefix":WORKBENCH_PREFIX,"meta":clean(meta or {}),"results":c}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (out/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['id','name','status','primary_metrics'])
        for r in c:
            metrics='; '.join(f"{k}={v}" for k,v in r['metrics'].items() if isinstance(v,(int,float,str)) and v is not None); w.writerow([r['id'],r['name'],r['status'],metrics])
    return out/'summary.json'
