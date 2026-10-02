from __future__ import annotations

import argparse
import json

from sst_horn_bem.core import run_horn_bem, write_json


def main() -> int:
    p = argparse.ArgumentParser(description="Run one SST horn-torus Neumann BEM audit")
    p.add_argument("--lambda", dest="lambda_", type=float, default=1.2)
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
    p.add_argument("--out", default="")
    args = p.parse_args()
    res = run_horn_bem(**vars(args) | {"out": None} if False else {
        "lambda_": args.lambda_,
        "n_ring": args.n_ring,
        "n_surface": args.n_surface,
        "n_volume": args.n_volume,
        "box_radius": args.box_radius,
        "source_eps": args.source_eps,
        "fd_step": args.fd_step,
        "bem": args.bem,
        "bem_n_eta": args.bem_n_eta,
        "bem_n_phi": args.bem_n_phi,
        "bem_self_term": args.bem_self_term,
        "bem_auto_self_term": args.bem_auto_self_term,
        "bem_ridge": args.bem_ridge,
        "force_python": args.force_python,
    })
    text = json.dumps(res, indent=2, allow_nan=True)
    print(text)
    if args.out:
        write_json(args.out, res)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
