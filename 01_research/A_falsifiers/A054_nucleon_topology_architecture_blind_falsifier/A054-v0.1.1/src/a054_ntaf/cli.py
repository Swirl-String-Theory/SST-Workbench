from __future__ import annotations
import argparse,os
from pathlib import Path
from .prepare import prepare
from .blind import run_blind
from .reveal import reveal

def main():
    p=argparse.ArgumentParser(prog='a054-ntaf'); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('prepare'); q.add_argument('--output',required=True); q.add_argument('--workbench'); q.add_argument('--n',type=int,default=144)
    q=sub.add_parser('blind'); q.add_argument('--campaign',required=True); q.add_argument('--config',required=True)
    q=sub.add_parser('reveal'); q.add_argument('--campaign',required=True)
    q=sub.add_parser('audit-pklsa'); q.add_argument('--workbench',required=True); q.add_argument('--output',required=True)
    a=p.parse_args()
    if a.cmd=='prepare':
        root=Path(a.workbench) if a.workbench else (Path(os.environ['SST_WORKBENCH_ROOT']) if os.environ.get('SST_WORKBENCH_ROOT') else None)
        print(prepare(Path(a.output),root,a.n))
    elif a.cmd=='blind': print(run_blind(Path(a.campaign),Path(a.config)))
    elif a.cmd=='reveal': print(reveal(Path(a.campaign)))
    else:
        from .pklsa import write_upstream_plan; print(write_upstream_plan(Path(a.workbench),Path(a.output)))
if __name__=='__main__': main()
