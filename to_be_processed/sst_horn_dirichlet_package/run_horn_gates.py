#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from sst_horn.horn_gates import HornGateConfig, run_gate, run_sweep, write_csv, write_json


def parse_args():
    p = argparse.ArgumentParser(description="SST horn-torus Dirichlet gate harness")
    p.add_argument("--lambda", dest="lambda_", type=float, default=1.2, help="torus major/minor ratio lambda > 1")
    p.add_argument("--sweep", type=float, nargs="*", help="lambda values for a sweep")
    p.add_argument("--n-ring", type=int, default=192)
    p.add_argument("--n-surface", type=int, default=40)
    p.add_argument("--n-volume", type=int, default=22)
    p.add_argument("--box-radius", type=float, default=6.0)
    p.add_argument("--eps", type=float, default=0.08, help="regularization radius for reference ring field")
    p.add_argument("--fd-step", type=float, default=0.025)
    p.add_argument("--force-rebuild", action="store_true")
    p.add_argument("--no-cpp", action="store_true", help="use NumPy fallback even if C++ extension is available")
    p.add_argument("--out", type=str, help="output basename; writes .json and .csv for sweeps")
    return p.parse_args()


def print_result(r):
    print("\n=== Horn Dirichlet Gate Result ===")
    for k, v in r.to_dict().items():
        print(f"{k:34s} {v}")


def main():
    a = parse_args()
    cfg = HornGateConfig(
        lambda_=a.lambda_,
        n_ring=a.n_ring,
        n_surface=a.n_surface,
        n_volume=a.n_volume,
        box_radius=a.box_radius,
        eps=a.eps,
        fd_step=a.fd_step,
        force_rebuild=a.force_rebuild,
        prefer_cpp=not a.no_cpp,
    )
    if a.sweep:
        results = run_sweep(a.sweep, cfg)
        for r in results:
            print_result(r)
        if a.out:
            base = Path(a.out)
            write_json(base.with_suffix(".json"), results)
            write_csv(base.with_suffix(".csv"), results)
            print(f"\nwrote {base.with_suffix('.json')} and {base.with_suffix('.csv')}")
    else:
        r = run_gate(cfg)
        print_result(r)
        if a.out:
            write_json(Path(a.out).with_suffix(".json"), r)
            print(f"\nwrote {Path(a.out).with_suffix('.json')}")


if __name__ == "__main__":
    main()
