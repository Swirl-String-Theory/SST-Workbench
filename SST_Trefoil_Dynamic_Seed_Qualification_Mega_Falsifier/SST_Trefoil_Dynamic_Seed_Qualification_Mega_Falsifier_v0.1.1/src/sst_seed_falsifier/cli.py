import argparse,sys
from pathlib import Path
from .io import load_json
from .candidates import generate
from .workflow import stage_early,stage_refine,stage_resolution,stage_core,stage_long,stage_rpo,stage_mechanism,reveal

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare');a.add_argument('dataset');a.add_argument('out');a.add_argument('config')
    for n in ['early','refine','resolution','core','long','rpo','mechanism']:
        a=sub.add_parser(n);a.add_argument('out');a.add_argument('config')
    a=sub.add_parser('reveal');a.add_argument('out')
    q=p.parse_args(argv)
    if q.cmd=='prepare': generate(q.dataset,q.out,load_json(q.config)); return 0
    fn={'early':stage_early,'refine':stage_refine,'resolution':stage_resolution,'core':stage_core,'long':stage_long,'rpo':stage_rpo,'mechanism':stage_mechanism}[q.cmd] if q.cmd!='reveal' else None
    if q.cmd=='reveal': reveal(q.out); return 0
    fn(q.out,load_json(q.config)); return 0
if __name__=='__main__': raise SystemExit(main())
