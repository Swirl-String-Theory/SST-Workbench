"""Optional resumable low-resolution Euler screen over the entire source corpus.

NOT part of the five-family high-resolution validation; can take hours on a CPU.
No source gets promoted to physical certification through this screening.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from .library_census import catalog
from .long_euler import run,ROOT

def screen_all(root=ROOT,grid=24,steps=72,duration=2.4,sigma=.5,max_cases=None,provider=None):
    approved={r['id']:r for r in json.loads((root/'results/GEOMETRY_CENSUS.json').read_text()) if r['geometry_status']=='SCREENING_COMPLETE'}
    items=[x for x in catalog(root) if x['id'] in approved and (not provider or x['provider']==provider)]
    if max_cases is not None: items=items[:max_cases]
    output=root/'results/EULER_ALL_SCREEN';output.mkdir(exist_ok=True)
    logpath=output/'QUEUE_EVENTS.jsonl';done={}
    if logpath.exists():
        for ln in logpath.read_text().splitlines():
            try:d=json.loads(ln);done[(d['id'],d['grid'],d['steps'],d['duration'],d['sigma'])]=d
            except Exception:pass
    queue_status=[]
    for i,x in enumerate(items):
        key=(x['id'],grid,steps,duration,sigma)
        if key in done:
            queue_status.append(done[key]);continue
        timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        try:
            r=run(x['curves'],name=x['id'],grid=grid,steps=steps,duration=duration,sigma=sigma,
                  output=output,source_sha256=x['sha256'])
            evt={'id':x['id'],'provider':x['provider'],'grid':grid,'steps':steps,'duration':duration,'sigma':sigma,
                 'status':'COMPUTED_EXPLORATORY','topology_screen':r['topology_unchanged_screen'],
                 'kelvin_drift':r['max_kelvin_loop_relative_drift'],'timestamp':timestamp}
        except Exception as ex:
            evt={'id':x['id'],'provider':x['provider'],'grid':grid,'steps':steps,'duration':duration,'sigma':sigma,
                 'status':'UNRESOLVED','reason':str(ex),'timestamp':timestamp}
        with logpath.open('a') as f:f.write(json.dumps(evt)+'\n')
        queue_status.append(evt)
        print(f'{i+1}/{len(items)} {x["id"]} : {evt["status"]}',flush=True)
    status={'queued':len(items),'computed':sum(x['status']=='COMPUTED_EXPLORATORY' for x in queue_status),
      'unresolved':sum(x['status']=='UNRESOLVED' for x in queue_status),
      'warning':'Single-grid screening cannot establish spatial/temporal convergence, and source variants are not independent providers.'}
    (output/'QUEUE_SUMMARY.json').write_text(json.dumps(status,indent=2))
    return status

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--grid',type=int,default=24)
    ap.add_argument('--steps',type=int,default=72);ap.add_argument('--duration',type=float,default=2.4)
    ap.add_argument('--sigma',type=float,default=.5);ap.add_argument('--max-cases',type=int,default=None)
    ap.add_argument('--provider',choices=['fremlin_fseries','fremlin_short_same_origin','ideal_links','knotplot_N300'])
    a=ap.parse_args()
    print(json.dumps(screen_all(grid=a.grid,steps=a.steps,duration=a.duration,sigma=a.sigma,max_cases=a.max_cases,provider=a.provider),indent=2))
