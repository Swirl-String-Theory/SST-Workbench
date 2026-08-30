import argparse,json,sys
from .util import clean_json
from pathlib import Path
from .workflow import run_prepare,run_candidates,run_analyze,reveal
from .resolution import compare as compare_resolution
from .stretch_compare import compare as compare_stretch

def main(argv=None):
    p=argparse.ArgumentParser(prog='sst-bsrp'); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare'); a.add_argument('dataset'); a.add_argument('work'); a.add_argument('config')
    a=sub.add_parser('run'); a.add_argument('work'); a.add_argument('config'); a.add_argument('--limit',type=int)
    a=sub.add_parser('analyze'); a.add_argument('work'); a.add_argument('config')
    a=sub.add_parser('reveal'); a.add_argument('work')
    a=sub.add_parser('resolution'); a.add_argument('work64'); a.add_argument('work96'); a.add_argument('work128'); a.add_argument('out')
    a=sub.add_parser('stretch-compare'); a.add_argument('material_work'); a.add_argument('fixed_work'); a.add_argument('out')
    ns=p.parse_args(argv)
    if ns.cmd=='prepare': out=run_prepare(ns.dataset,ns.work,ns.config)
    elif ns.cmd=='run': out=run_candidates(ns.work,ns.config,ns.limit)
    elif ns.cmd=='analyze': out=run_analyze(ns.work,ns.config)
    elif ns.cmd=='reveal': out=reveal(ns.work)
    elif ns.cmd=='resolution': out=compare_resolution(ns.work64,ns.work96,ns.work128,ns.out)
    else: out=compare_stretch(ns.material_work,ns.fixed_work,ns.out)
    print(json.dumps(clean_json(out),indent=2,sort_keys=True,allow_nan=False)); return 0
if __name__=='__main__': raise SystemExit(main())
