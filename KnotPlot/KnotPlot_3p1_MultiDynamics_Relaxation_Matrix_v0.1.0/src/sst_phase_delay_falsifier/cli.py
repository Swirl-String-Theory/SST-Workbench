from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .blind import prepare
from .analysis import load_cfg,predict_all,measure_all,evaluate,reveal
from .backend import BACKEND

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('backend'); q.add_argument('--require-cpp',action='store_true')
    q=sub.add_parser('prepare'); q.add_argument('--input',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True)
    q=sub.add_parser('predict'); q.add_argument('--blind',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True)
    q=sub.add_parser('measure'); q.add_argument('--blind',required=True);q.add_argument('--out',required=True);q.add_argument('--config',required=True)
    q=sub.add_parser('evaluate'); q.add_argument('--pred',required=True);q.add_argument('--measure',required=True);q.add_argument('--out',required=True)
    q=sub.add_parser('reveal'); q.add_argument('--eval',required=True);q.add_argument('--key',required=True);q.add_argument('--out',required=True)
    a=p.parse_args(argv)
    if a.cmd=='backend':
        print(BACKEND); return 0 if (not a.require_cpp or BACKEND=='cpp') else 2
    if a.cmd=='prepare':
        c=load_cfg(a.config); print('prepared',prepare(a.input,a.out,c['input']['pattern'],c['geometry']['n_points'])); return 0
    if a.cmd=='predict': predict_all(a.blind,load_cfg(a.config),a.out); return 0
    if a.cmd=='measure': measure_all(a.blind,load_cfg(a.config),a.out); return 0
    if a.cmd=='evaluate':
        r=evaluate(a.pred,a.measure,a.out); print(json.dumps(r,indent=2)); return 0 if r['status'] in ('PASS','INCONCLUSIVE') else 3
    if a.cmd=='reveal': reveal(a.eval,a.key,a.out); return 0
if __name__=='__main__': raise SystemExit(main())
