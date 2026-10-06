from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
from .synthetic import make_reference_panel
from .evaluation import evaluate
from .io import load_manifest
from .upstream import audit_snapshot

def load_config(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding='utf-8')

def cmd_synthetic(args):
    cfg=load_config(args.config); out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    m,t,e,en=make_reference_panel(n_pairs=args.pairs,steps=args.steps,dt=args.dt,seed=args.seed)
    np.savez_compressed(out/'synthetic_reference.npz',t=t,eta=e,energy=en)
    m['arrays_file']='synthetic_reference.npz'; write_json(out/'synthetic_manifest.json',m)
    r=evaluate(m,t,e,en,cfg); write_json(out/'blind_results.json',r)
    print(json.dumps({'verdict':r['verdict'],'physics_verdict':r['physics_verdict']},indent=2))
    return 0 if r['verdict']=='QUALIFIED_INSTRUMENT_ONLY' else 2

def cmd_physical(args):
    cfg=load_config(args.config); m,t,e,en,res=load_manifest(args.manifest); r=evaluate(m,t,e,en,cfg,res)
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True); write_json(out/'blind_results.json',r)
    print(json.dumps({'verdict':r['verdict'],'physics_verdict':r['physics_verdict']},indent=2)); return 0 if r['verdict']!='SYNTHETIC_QUALIFICATION_FAILED' else 2

def cmd_upstream(args):
    r=audit_snapshot(args.snapshot); write_json(args.output,r); print(json.dumps(r,indent=2)); return 0

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--config',default=str(Path(__file__).resolve().parents[1]/'configs'/'default.json'))
    sp=p.add_subparsers(dest='cmd',required=True)
    s=sp.add_parser('synthetic'); s.add_argument('--output-dir',required=True); s.add_argument('--pairs',type=int,default=24); s.add_argument('--steps',type=int,default=4000); s.add_argument('--dt',type=float,default=0.01); s.add_argument('--seed',type=int,default=5101); s.set_defaults(fn=cmd_synthetic)
    q=sp.add_parser('physical'); q.add_argument('--manifest',required=True); q.add_argument('--output-dir',required=True); q.set_defaults(fn=cmd_physical)
    u=sp.add_parser('upstream-audit'); u.add_argument('--snapshot',required=True); u.add_argument('--output',required=True); u.set_defaults(fn=cmd_upstream)
    a=p.parse_args(argv); return a.fn(a)
if __name__=='__main__': raise SystemExit(main())
