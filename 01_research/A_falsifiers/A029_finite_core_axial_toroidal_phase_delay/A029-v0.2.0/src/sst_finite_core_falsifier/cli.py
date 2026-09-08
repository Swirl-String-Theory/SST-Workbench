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
    sp.add_parser('backend');a=ap.parse_args()
    if a.cmd=='prepare':r=prepare(a.root,a.out,a.config)
    elif a.cmd=='blind':r=run_blind(a.root,Path(a.campaign)/'blind_catalog',a.out,a.config,a.limit)
    elif a.cmd=='reveal':r=reveal(a.root,a.blind,Path(a.campaign)/'blind_catalog',a.config,Path(a.campaign)/'private',a.out)
    else:r={'backend':backend_name()}
    print(json.dumps(r,indent=2,sort_keys=True,allow_nan=True))
if __name__=='__main__':main()
