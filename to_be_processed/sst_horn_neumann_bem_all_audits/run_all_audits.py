from __future__ import annotations
import argparse, json
from pathlib import Path
from sst_horn_bem.core import run_horn_bem, run_sweep, write_csv, write_json
from sst_horn_bem.audits import run_panel_refinement, run_volume_refinement, run_offset_probe_audit, summarize_all

def parse_lambdas(s: str): return [float(x.strip()) for x in s.split(',') if x.strip()]
def parse_grids(s: str):
    out=[]
    for part in s.split(','):
        part=part.strip().lower().replace('x',':')
        if not part: continue
        a,b=part.split(':')
        out.append((int(a), int(b)))
    return out
def parse_ints(s: str): return [int(x.strip()) for x in s.split(',') if x.strip()]

def main() -> int:
    p=argparse.ArgumentParser(description='Regenerate ring-only, BEM, sweep, and all numerical audits')
    p.add_argument('--lambda', dest='lambda_', type=float, default=1.2)
    p.add_argument('--lambdas', default='1.05,1.1,1.2,1.5,2.0')
    p.add_argument('--panel-grids', default='8x16,12x24,16x32')
    p.add_argument('--n-volumes', default='14,18,22')
    p.add_argument('--n-ring', type=int, default=256)
    p.add_argument('--n-surface', type=int, default=32)
    p.add_argument('--n-volume', type=int, default=18)
    p.add_argument('--bem-n-eta', type=int, default=12)
    p.add_argument('--bem-n-phi', type=int, default=24)
    p.add_argument('--box-radius', type=float, default=6.0)
    p.add_argument('--source-eps', type=float, default=0.08)
    p.add_argument('--force-python', action='store_true')
    p.add_argument('--out-dir', default='audit_out')
    args=p.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    common=dict(n_ring=args.n_ring, n_surface=args.n_surface, n_volume=args.n_volume, box_radius=args.box_radius, source_eps=args.source_eps, force_python=args.force_python)
    bem_common=dict(**common, bem_n_eta=args.bem_n_eta, bem_n_phi=args.bem_n_phi)

    ring=run_horn_bem(lambda_=args.lambda_, bem=False, **common)
    bem=run_horn_bem(lambda_=args.lambda_, bem=True, **bem_common)
    sweep=run_sweep(lambdas=parse_lambdas(args.lambdas), bem=True, **bem_common)
    panel=run_panel_refinement(lambda_=args.lambda_, panel_grids=parse_grids(args.panel_grids), **common)
    volume=run_volume_refinement(lambda_=args.lambda_, n_volumes=parse_ints(args.n_volumes), n_ring=args.n_ring, n_surface=args.n_surface, bem_n_eta=args.bem_n_eta, bem_n_phi=args.bem_n_phi, box_radius=args.box_radius, source_eps=args.source_eps, force_python=args.force_python)
    offset=run_offset_probe_audit(lambda_=args.lambda_, **bem_common)
    summary=summarize_all(ring, bem, sweep, panel, volume, offset)

    write_json(out/'horn_ring_reference.json', ring)
    write_json(out/'horn_bem_reference.json', bem)
    write_json(out/'horn_bem_sweep.json', sweep); write_csv(out/'horn_bem_sweep.csv', sweep)
    write_json(out/'horn_panel_refinement.json', panel); write_csv(out/'horn_panel_refinement.csv', panel)
    write_json(out/'horn_volume_refinement.json', volume); write_csv(out/'horn_volume_refinement.csv', volume)
    write_json(out/'horn_offset_probe.json', offset); write_csv(out/'horn_offset_probe.csv', offset.get('offset_probe', []))
    write_json(out/'audit_summary.json', summary)
    print(json.dumps(summary, indent=2, allow_nan=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
