from __future__ import annotations
import argparse,os
from pathlib import Path
from .prepare import prepare
from .blind import run_blind
from .reveal import reveal
from .prepare_v020 import prepare_certification
from .certify_v020 import run_certification
from .reveal_v020 import reveal_certification


def main():
    p=argparse.ArgumentParser(prog='a054-ntaf'); sub=p.add_subparsers(dest='cmd',required=True)
    q=sub.add_parser('prepare'); q.add_argument('--output',required=True); q.add_argument('--workbench'); q.add_argument('--n',type=int,default=144)
    q=sub.add_parser('blind'); q.add_argument('--campaign',required=True); q.add_argument('--config',required=True)
    q=sub.add_parser('reveal'); q.add_argument('--campaign',required=True)
    q=sub.add_parser('prepare-cert'); q.add_argument('--output',required=True); q.add_argument('--workbench',required=True); q.add_argument('--n',type=int,default=96); q.add_argument('--preset',choices=['basic','extended','full'],default='basic')
    q=sub.add_parser('certify'); q.add_argument('--campaign',required=True); q.add_argument('--config',required=True)
    q=sub.add_parser('reveal-cert'); q.add_argument('--campaign',required=True)
    q=sub.add_parser('audit-pklsa'); q.add_argument('--workbench',required=True); q.add_argument('--output',required=True)
    a=p.parse_args()
    if a.cmd=='prepare':
        root=Path(a.workbench) if a.workbench else (Path(os.environ['SST_WORKBENCH_ROOT']) if os.environ.get('SST_WORKBENCH_ROOT') else None)
        print(prepare(Path(a.output),root,a.n))
    elif a.cmd=='blind': print(run_blind(Path(a.campaign),Path(a.config)))
    elif a.cmd=='reveal': print(reveal(Path(a.campaign)))
    elif a.cmd=='prepare-cert': print(prepare_certification(Path(a.output),Path(a.workbench),a.n,a.preset))
    elif a.cmd=='certify': print(run_certification(Path(a.campaign),Path(a.config)))
    elif a.cmd=='reveal-cert': print(reveal_certification(Path(a.campaign)))
    else:
        from .pklsa import write_upstream_plan; print(write_upstream_plan(Path(a.workbench),Path(a.output)))
if __name__=='__main__': main()
