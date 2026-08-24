from __future__ import annotations
import argparse,json
from pathlib import Path
from .blind import prepare
from .analysis import load_cfg,predict_all,measure_all,evaluate,reveal,preparation_audit,_json_safe
from .backend import BACKEND

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('backend'); q.add_argument('--require-cpp',action='store_true')
    q=sub.add_parser('prepare'); q.add_argument('--input',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True);q.add_argument('--mode',choices=['confirmatory','legacy_audit'],default='confirmatory')
    q=sub.add_parser('predict'); q.add_argument('--blind',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True)
    q=sub.add_parser('measure'); q.add_argument('--blind',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True)
    q=sub.add_parser('evaluate'); q.add_argument('--pred',required=True);q.add_argument('--measure',required=True);q.add_argument('--manifest',required=True);q.add_argument('--audit',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('reveal'); q.add_argument('--eval',required=True);q.add_argument('--key',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('prep-audit'); q.add_argument('--key',required=True);q.add_argument('--out',required=True)
    a=p.parse_args(argv)
    if a.cmd=='backend': print(BACKEND); return 0 if (not a.require_cpp or BACKEND=='cpp') else 2
    if a.cmd=='prepare':
        c=load_cfg(a.config); root=Path(a.config).resolve().parents[1]
        reg=root/c['dataset']['historical_registry']
        r=prepare(a.input,a.out,c['input']['pattern'],c['geometry']['n_points'],c['dataset']['identity_hash_points'],c['dataset']['novelty_hash_points'],a.mode,reg,c['gates']['min_candidates'])
        print(json.dumps(r,indent=2)); return 0
    if a.cmd=='predict': predict_all(a.blind,load_cfg(a.config),a.out); return 0
    if a.cmd=='measure': measure_all(a.blind,load_cfg(a.config),a.out); return 0
    if a.cmd=='evaluate':
        r=evaluate(a.pred,a.measure,a.manifest,a.audit,a.out); print(json.dumps(_json_safe(r),indent=2,allow_nan=False)); return 0 if r['status'] in ('PASS','INCONCLUSIVE') else 3
    if a.cmd=='reveal': reveal(a.eval,a.key,a.out); return 0
    if a.cmd=='prep-audit': preparation_audit(a.key,a.out); return 0
if __name__=='__main__': raise SystemExit(main())
