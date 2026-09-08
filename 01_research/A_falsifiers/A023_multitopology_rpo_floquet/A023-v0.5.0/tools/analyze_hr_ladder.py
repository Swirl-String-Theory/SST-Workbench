from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from sst_blind.ladder import analyze_ladder, write_ladder_outputs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out_dir'); ap.add_argument('--plan',default='configs/hr_ladder/ladder_plan.json'); a=ap.parse_args()
    out=Path(a.out_dir); plan=json.loads(Path(a.plan).read_text(encoding='utf-8')); payload={}
    for rd in plan['rungs']:
        ro=out/f"{rd['index']:02d}_{rd['name']}"; mf=ro/'unblind_manifest.json'; pre=ro/'pre_unblind'; vf=ro/'final_verdict.json'
        if not (mf.exists() and pre.exists() and vf.exists()): raise SystemExit(f'missing completed rung: {ro}')
        mapping=json.loads(mf.read_text(encoding='utf-8')); results={}
        for af in sorted(pre.glob('B*_analysis.json')): results[af.stem.replace('_analysis','')]=json.loads(af.read_text(encoding='utf-8'))
        payload[rd['name']]={'mapping':mapping,'results':results,'final':json.loads(vf.read_text(encoding='utf-8'))}
    records=analyze_ladder(payload,plan); s=write_ladder_outputs(out,records,plan); print(json.dumps({'counts':s['counts'],'datasets':len(records),'out_dir':str(out)},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
