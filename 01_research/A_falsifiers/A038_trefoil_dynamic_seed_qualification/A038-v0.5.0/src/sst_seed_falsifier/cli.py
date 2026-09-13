import argparse
from .io import load_json
from .candidates import generate
from .evidence import validate_frozen_evidence
from .modal_dispatch import enforce_modal_dispatch
from .workflow import stage_early,stage_refine,stage_resolution,stage_temporal,stage_core,stage_mesh_gauge,stage_mesh_closure,stage_operator_split,stage_long,stage_rpo,stage_mechanism,reveal


def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare'); a.add_argument('dataset'); a.add_argument('out'); a.add_argument('config')
    for n in ['early','refine','resolution','temporal','core','mesh-gauge','mesh-closure','operator-split','long','rpo','mechanism']:
        a=sub.add_parser(n); a.add_argument('out'); a.add_argument('config')
    a=sub.add_parser('reveal'); a.add_argument('out')
    a=sub.add_parser('modal-dispatch'); a.add_argument('out'); a.add_argument('config')
    q=p.parse_args(argv)
    if q.cmd=='prepare': generate(q.dataset,q.out,load_json(q.config),config_path=q.config); return 0
    if q.cmd=='reveal': reveal(q.out); return 0
    if q.cmd=='modal-dispatch':
        enforce_modal_dispatch(q.out, load_json(q.config)); return 0
    fn={'early':stage_early,'refine':stage_refine,'resolution':stage_resolution,'temporal':stage_temporal,'core':stage_core,'mesh-gauge':stage_mesh_gauge,'mesh-closure':stage_mesh_closure,'operator-split':stage_operator_split,'long':stage_long,'rpo':stage_rpo,'mechanism':stage_mechanism}[q.cmd]
    cfg=load_json(q.config); enforce_modal_dispatch(q.out, cfg); validate_frozen_evidence(q.out,cfg,q.config)
    fn(q.out,cfg); return 0


if __name__=='__main__': raise SystemExit(main())
