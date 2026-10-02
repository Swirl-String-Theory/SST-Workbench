from __future__ import annotations
import argparse, json
from sst_horn_bem.audits import run_panel_refinement
from sst_horn_bem.core import write_csv, write_json

def parse_grids(s: str):
    out=[]
    for part in s.split(','):
        part=part.strip().lower().replace('x',':')
        if not part: continue
        a,b=part.split(':')
        out.append((int(a), int(b)))
    return out

def main() -> int:
    p=argparse.ArgumentParser(description='BEM panel-refinement audit')
    p.add_argument('--lambda', dest='lambda_', type=float, default=1.2)
    p.add_argument('--panel-grids', default='8x16,12x24,16x32')
    p.add_argument('--n-ring', type=int, default=256)
    p.add_argument('--n-surface', type=int, default=32)
    p.add_argument('--n-volume', type=int, default=18)
    p.add_argument('--box-radius', type=float, default=6.0)
    p.add_argument('--source-eps', type=float, default=0.08)
    p.add_argument('--force-python', action='store_true')
    p.add_argument('--out-json', default='horn_panel_refinement.json')
    p.add_argument('--out-csv', default='horn_panel_refinement.csv')
    args=p.parse_args()
    rows=run_panel_refinement(lambda_=args.lambda_, panel_grids=parse_grids(args.panel_grids), n_ring=args.n_ring, n_surface=args.n_surface, n_volume=args.n_volume, box_radius=args.box_radius, source_eps=args.source_eps, force_python=args.force_python)
    print(json.dumps(rows, indent=2, allow_nan=True))
    write_json(args.out_json, rows); write_csv(args.out_csv, rows)
    return 0
if __name__=='__main__': raise SystemExit(main())
