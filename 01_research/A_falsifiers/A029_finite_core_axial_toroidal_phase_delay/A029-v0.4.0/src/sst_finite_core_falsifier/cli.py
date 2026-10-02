from __future__ import annotations
from pathlib import Path
import argparse,json
from .prepare import prepare
from .workflow import run_blind
from .reveal import reveal
from .native import backend_name

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    p=sp.add_parser('prepare');p.add_argument('--root',default='.');p.add_argument('--out',required=True);p.add_argument('--config',required=True)
    p=sp.add_parser('blind');p.add_argument('--root',default='.');p.add_argument('--campaign',required=True);p.add_argument('--out',required=True);p.add_argument('--config',required=True);p.add_argument('--limit',type=int)
    p=sp.add_parser('reveal');p.add_argument('--root',default='.');p.add_argument('--campaign',required=True);p.add_argument('--blind',required=True);p.add_argument('--out',required=True);p.add_argument('--config',required=True)
    p=sp.add_parser('phase-residual');p.add_argument('--out',required=True);p.add_argument('--config');p.add_argument('--enable',action='store_true');p.add_argument('--pack-root',default='.');p.add_argument('--historical-root',action='append',default=None);p.add_argument('--no-default-historical',action='store_true')
    p=sp.add_parser('independent-residual');p.add_argument('--out',required=True);p.add_argument('--config');p.add_argument('--enable',action='store_true');p.add_argument('--pack-root',default='.');p.add_argument('--historical-root',action='append',default=None);p.add_argument('--no-default-historical',action='store_true')
    sp.add_parser('backend');a=ap.parse_args()
    if a.cmd=='prepare':r=prepare(a.root,a.out,a.config)
    elif a.cmd=='blind':r=run_blind(a.root,Path(a.campaign)/'blind_catalog',a.out,a.config,a.limit)
    elif a.cmd=='reveal':r=reveal(a.root,a.blind,Path(a.campaign)/'blind_catalog',a.config,Path(a.campaign)/'private',a.out)
    elif a.cmd in {'phase-residual','independent-residual'}:
        from .residual import run_phase_residual
        cfg=json.loads(Path(a.config).read_text(encoding='utf-8')) if a.config else {}
        if a.enable: cfg['enable_phase_residual_v1']=True
        r=run_phase_residual(a.out,pack_root=a.pack_root,cfg=cfg,historical_roots=a.historical_root,search_default_historical=not a.no_default_historical)
    else:r={'backend':backend_name()}
    print(json.dumps(r,indent=2,sort_keys=True,allow_nan=True))
if __name__=='__main__':main()
