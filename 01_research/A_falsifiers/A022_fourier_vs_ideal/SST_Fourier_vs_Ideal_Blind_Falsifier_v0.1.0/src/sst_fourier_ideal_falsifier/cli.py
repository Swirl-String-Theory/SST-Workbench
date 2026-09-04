from __future__ import annotations
import argparse,json
from pathlib import Path
from .prepare import prepare,discover_source_paths
from .workflow import run_blind
from .reveal import reveal
from .native import backend_name

def main(argv=None):
    p=argparse.ArgumentParser(prog='sst-fvi',description='Blind Fourier-series vs ideal vortex-knot dynamical falsifier')
    sp=p.add_subparsers(dest='cmd',required=True)
    q=sp.add_parser('backend')
    q=sp.add_parser('sources');q.add_argument('--base',default='.');q.add_argument('--ideal');q.add_argument('--ideal-js');q.add_argument('--fseries-root');q.add_argument('--relaxed-root')
    q=sp.add_parser('prepare');q.add_argument('--out',default='.');q.add_argument('--base',default='.');q.add_argument('--ideal');q.add_argument('--ideal-js');q.add_argument('--fseries-root');q.add_argument('--relaxed-root');q.add_argument('--mode',choices=['torus','all'],default='torus');q.add_argument('--n',type=int,default=192);q.add_argument('--seed',type=int,default=1729);q.add_argument('--include-variants',action='store_true');q.add_argument('--include-relaxed-control',action='store_true')
    q=sp.add_parser('run');q.add_argument('--project-root',default='.');q.add_argument('--catalog',default='blind_catalog');q.add_argument('--out',required=True);q.add_argument('--config',required=True);q.add_argument('--limit',type=int)
    q=sp.add_parser('reveal');q.add_argument('--project-root',default='.');q.add_argument('--blind',required=True);q.add_argument('--catalog',default='blind_catalog');q.add_argument('--config',required=True);q.add_argument('--private',default='private');q.add_argument('--out',required=True)
    a=p.parse_args(argv)
    if a.cmd=='backend':print(backend_name());return 0
    if a.cmd=='sources':print(json.dumps(discover_source_paths(a.base,a.ideal,a.ideal_js,a.fseries_root,a.relaxed_root),indent=2));return 0
    if a.cmd=='prepare':print(json.dumps(prepare(a.out,a.base,a.ideal,a.ideal_js,a.fseries_root,a.relaxed_root,a.mode,a.n,a.seed,a.include_variants,a.include_relaxed_control),indent=2));return 0
    if a.cmd=='run':print(json.dumps(run_blind(a.project_root,a.catalog,a.out,a.config,a.limit),indent=2));return 0
    if a.cmd=='reveal':print(json.dumps(reveal(a.project_root,a.blind,a.catalog,a.config,a.private,a.out),indent=2,allow_nan=True));return 0
    return 2
if __name__=='__main__':raise SystemExit(main())
