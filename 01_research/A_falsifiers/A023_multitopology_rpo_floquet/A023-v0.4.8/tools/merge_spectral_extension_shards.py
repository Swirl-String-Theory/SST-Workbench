from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sst_blind.spectral_extension import write_extension_outputs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out_dir'); ap.add_argument('shards',nargs='+'); ap.add_argument('--plan',default='configs/spectral_extension/spectral_extension_plan.json'); a=ap.parse_args()
    plan=json.loads(Path(a.plan).read_text(encoding='utf-8')); records=[]; seen=set()
    for sp in a.shards:
        p=Path(sp)/'SPECTRAL_EXTENSION_RESULTS.json'
        if not p.exists(): raise SystemExit(f'missing shard result: {p}')
        obj=json.loads(p.read_text(encoding='utf-8'))
        if obj.get('version')!=plan['version']: raise SystemExit(f'version mismatch: {p}')
        for r in obj['records']:
            if r['source'] in seen: raise SystemExit(f'duplicate source across shards: {r["source"]}')
            seen.add(r['source']); records.append(r)
    records.sort(key=lambda r:r['source'])
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    write_extension_outputs(out,records,plan)
    (out/'MERGED_SHARDS.json').write_text(json.dumps({'shards':a.shards,'records':len(records)},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'merged':len(records),'out_dir':str(out)},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
