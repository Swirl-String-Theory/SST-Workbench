from __future__ import annotations
import argparse, json
from sst_horn_bem.audits import run_volume_refinement
from sst_horn_bem.core import write_csv, write_json

def parse_ints(s: str): return [int(x.strip()) for x in s.split(',') if x.strip()]

def main() -> int:
    p=argparse.ArgumentParser(description='Volume integration refinement audit')
    p.add_argument('--lambda', dest='lambda_', type=float, default=1.2)
    p.add_argument('--n-volumes', default='14,18,22')
    p.add_argument('--n-ring', type=int, default=256)
    p.add_argument('--n-surface', type=int, default=32)
    p.add_argument('--bem-n-eta', type=int, default=12)
    p.add_argument('--bem-n-phi', type=int, default=24)
    p.add_argument('--box-radius', type=float, default=6.0)
    p.add_argument('--source-eps', type=float, default=0.08)
    p.add_argument('--force-python', action='store_true')
    p.add_argument('--out-json', default='horn_volume_refinement.json')
    p.add_argument('--out-csv', default='horn_volume_refinement.csv')
    args=p.parse_args()
    rows=run_volume_refinement(lambda_=args.lambda_, n_volumes=parse_ints(args.n_volumes), n_ring=args.n_ring, n_surface=args.n_surface, bem_n_eta=args.bem_n_eta, bem_n_phi=args.bem_n_phi, box_radius=args.box_radius, source_eps=args.source_eps, force_python=args.force_python)
    print(json.dumps(rows, indent=2, allow_nan=True))
    write_json(args.out_json, rows); write_csv(args.out_csv, rows)
    return 0
if __name__=='__main__': raise SystemExit(main())
