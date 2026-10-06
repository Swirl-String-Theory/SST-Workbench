from __future__ import annotations
import argparse, json
from pathlib import Path
from .evaluator import evaluate_manifest
from .selftest_data import instrument_manifest
from .workbench import discover_plan
from .reveal import reveal

def loadj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dumpj(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def main(argv=None):
    ap=argparse.ArgumentParser(prog='a053-etptf')
    sp=ap.add_subparsers(dest='cmd',required=True)
    p=sp.add_parser('selftest'); p.add_argument('--config',default='configs/basic.json'); p.add_argument('--output-dir',default='outputs/selftest')
    p=sp.add_parser('evaluate'); p.add_argument('--manifest',required=True); p.add_argument('--config',default='configs/basic.json'); p.add_argument('--output-dir',required=True)
    p=sp.add_parser('plan'); p.add_argument('--workbench-root',required=True); p.add_argument('--output',default='outputs/WORKBENCH_PLAN.json')
    p=sp.add_parser('reveal'); p.add_argument('--summary',required=True); p.add_argument('--config',required=True); p.add_argument('--output',default='outputs/reveal/REVEAL.json')
    a=ap.parse_args(argv)
    if a.cmd=='selftest':
        m=instrument_manifest(); cfg=loadj(a.config); out=evaluate_manifest(m,cfg); od=Path(a.output_dir); dumpj(od/'SELFTEST_MANIFEST.json',m); dumpj(od/'TOURNAMENT_SUMMARY.json',out); print(out['verdict'],out['survivors'])
    elif a.cmd=='evaluate':
        m=loadj(a.manifest); cfg=loadj(a.config); out=evaluate_manifest(m,cfg); od=Path(a.output_dir); dumpj(od/'TOURNAMENT_SUMMARY.json',out); print(out['verdict'],out['survivors'])
    elif a.cmd=='plan':
        out=discover_plan(a.workbench_root); dumpj(a.output,out); print('blockers=',out['blockers'])
    else:
        out=reveal(a.summary,a.config); dumpj(a.output,out); print('reveal attached to',out['blind_summary_sha256'])

if __name__=='__main__': main()
