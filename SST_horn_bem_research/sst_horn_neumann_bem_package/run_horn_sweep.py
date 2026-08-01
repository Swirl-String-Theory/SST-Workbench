from __future__ import annotations

import argparse
import json

from sst_horn_bem.core import run_sweep, write_csv, write_json


def parse_lambdas(s: str):
    return [float(x.strip()) for x in s.split(",") if x.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Run a lambda sweep for the SST horn-torus Neumann BEM audit")
    p.add_argument("--lambdas", default="1.05,1.1,1.2,1.5,2.0")
    p.add_argument("--n-ring", type=int, default=256)
    p.add_argument("--n-surface", type=int, default=32)
    p.add_argument("--n-volume", type=int, default=18)
    p.add_argument("--box-radius", type=float, default=6.0)
    p.add_argument("--source-eps", type=float, default=0.08)
    p.add_argument("--fd-step", type=float, default=1e-3)
    p.add_argument("--bem", action="store_true", default=True)
    p.add_argument("--no-bem", dest="bem", action="store_false")
    p.add_argument("--bem-n-eta", type=int, default=12)
    p.add_argument("--bem-n-phi", type=int, default=24)
    p.add_argument("--bem-self-term", type=float, default=0.5)
    p.add_argument("--no-auto-self-term", dest="bem_auto_self_term", action="store_false", default=True)
    p.add_argument("--bem-ridge", type=float, default=1e-10)
    p.add_argument("--force-python", action="store_true")
    p.add_argument("--out-json", default="horn_bem_sweep.json")
    p.add_argument("--out-csv", default="horn_bem_sweep.csv")
    args = p.parse_args()
    rows = run_sweep(
        lambdas=parse_lambdas(args.lambdas),
        n_ring=args.n_ring,
        n_surface=args.n_surface,
        n_volume=args.n_volume,
        box_radius=args.box_radius,
        source_eps=args.source_eps,
        fd_step=args.fd_step,
        bem=args.bem,
        bem_n_eta=args.bem_n_eta,
        bem_n_phi=args.bem_n_phi,
        bem_self_term=args.bem_self_term,
        bem_auto_self_term=args.bem_auto_self_term,
        bem_ridge=args.bem_ridge,
        force_python=args.force_python,
    )
    print(json.dumps(rows, indent=2, allow_nan=True))
    write_json(args.out_json, rows)
    write_csv(args.out_csv, rows)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
