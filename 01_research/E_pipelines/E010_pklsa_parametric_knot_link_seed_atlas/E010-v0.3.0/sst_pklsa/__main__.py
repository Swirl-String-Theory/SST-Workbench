from __future__ import annotations
import argparse, json, gzip
from pathlib import Path
from .core import Workbench

def write_json(obj, path):
    data=json.dumps(obj,indent=2,sort_keys=True)
    if not path:
        print(data); return
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if p.suffix=='.gz':
        with gzip.open(p,'wt',encoding='utf-8') as f:f.write(data)
    else:p.write_text(data,encoding='utf-8')

def main(argv=None):
    ap=argparse.ArgumentParser(prog='sst_pklsa')
    ap.add_argument('--workbench',required=True)
    ap.add_argument('--contract')
    sub=ap.add_subparsers(dest='cmd',required=True)
    d=sub.add_parser('doctor'); d.add_argument('--output')
    r=sub.add_parser('resolve'); r.add_argument('--output')
    i=sub.add_parser('inventory'); i.add_argument('--deep-hash',action='store_true'); i.add_argument('--output')
    b=sub.add_parser('bridges'); b.add_argument('--output')
    q=sub.add_parser('qualify'); q.add_argument('--base',required=True); q.add_argument('--topology',default='3_1'); q.add_argument('--config',default='configs/qualification_basic.json'); q.add_argument('--out',required=True); q.add_argument('--publication',action='store_true')
    a=ap.parse_args(argv)
    wb=Workbench.open(a.workbench,a.contract) if a.contract else Workbench.open(a.workbench)
    if a.cmd=='doctor': write_json(wb.doctor(),a.output); return 0
    if a.cmd=='resolve': write_json({'schema':'SST-PKLSA-RESOLUTION-1','sources':[s.__dict__ for s in wb.resolve_sources()]},a.output); return 0
    if a.cmd=='inventory': write_json(wb.inventory(a.deep_hash),a.output); return 0
    if a.cmd=='bridges': write_json(wb.bridges(),a.output); return 0
    if a.cmd=='qualify':
        # Reuse proven qualification core; the base is historical PKLSA v0.2.0 or extracted equivalent.
        from pklsa_builder.models import QualificationConfig
        from pklsa_builder.builder import build_release
        cfg=QualificationConfig.load(a.config)
        out=build_release(base=a.base,output=a.out,config=cfg,workbench_root=None,topologies=[a.topology],strict_source_coverage=False)
        # Store repo-native source-resolution audit alongside qualification output.
        Path(a.out).mkdir(parents=True,exist_ok=True)
        write_json(wb.doctor(),str(Path(a.out)/'WORKBENCH_SOURCE_RESOLUTION.json'))
        write_json(out,str(Path(a.out)/'QUALIFICATION_RELEASE.json'))
        return 0
    return 2

if __name__=='__main__': raise SystemExit(main())
