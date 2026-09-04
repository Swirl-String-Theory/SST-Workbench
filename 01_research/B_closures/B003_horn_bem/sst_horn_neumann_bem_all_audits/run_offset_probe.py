from __future__ import annotations
import argparse, json
from sst_horn_bem.audits import run_offset_probe_audit
from sst_horn_bem.core import write_csv, write_json

def main() -> int:
    p=argparse.ArgumentParser(description='One-sided exterior offset-boundary probe audit')
    p.add_argument('--lambda', dest='lambda_', type=float, default=1.2)
    p.add_argument('--n-ring', type=int, default=256)
    p.add_argument('--n-surface', type=int, default=32)
    p.add_argument('--n-volume', type=int, default=18)
    p.add_argument('--bem-n-eta', type=int, default=12)
    p.add_argument('--bem-n-phi', type=int, default=24)
    p.add_argument('--box-radius', type=float, default=6.0)
    p.add_argument('--source-eps', type=float, default=0.08)
    p.add_argument('--force-python', action='store_true')
    p.add_argument('--out-json', default='horn_offset_probe.json')
    p.add_argument('--out-csv', default='horn_offset_probe.csv')
    args=p.parse_args()
    res=run_offset_probe_audit(lambda_=args.lambda_, n_ring=args.n_ring, n_surface=args.n_surface, n_volume=args.n_volume, bem_n_eta=args.bem_n_eta, bem_n_phi=args.bem_n_phi, box_radius=args.box_radius, source_eps=args.source_eps, force_python=args.force_python)
    print(json.dumps(res, indent=2, allow_nan=True))
    write_json(args.out_json, res); write_csv(args.out_csv, res.get('offset_probe', []))
    return 0
if __name__=='__main__': raise SystemExit(main())
