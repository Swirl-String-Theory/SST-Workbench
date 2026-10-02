from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sst_blind.ladder import write_ladder_outputs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out_dir'); ap.add_argument('shards',nargs='+'); ap.add_argument('--plan',default='configs/hr_ladder/ladder_plan.json'); a=ap.parse_args()
    plan=json.loads(Path(a.plan).read_text(encoding='utf-8')); recs=[]; seen=set()
    for sd in map(Path,a.shards):
        f=sd/'LADDER_RESULTS.json'
        if not f.exists(): raise SystemExit(f'missing {f}; run run_hr_ladder_analyze.cmd first if needed')
        d=json.loads(f.read_text(encoding='utf-8'))
        for r in d['records']:
            src=r['source']
            if src in seen: raise SystemExit(f'duplicate source across shards: {src}')
            seen.add(src); recs.append(r)
    s=write_ladder_outputs(a.out_dir,recs,plan)
    print(json.dumps({'shards':len(a.shards),'datasets':len(recs),'counts':s['counts'],'out_dir':a.out_dir},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
