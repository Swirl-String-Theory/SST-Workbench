#!/usr/bin/env python3
"""Run the pre-registered director/Hodge convergence ladder in blind mode."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

from blind_utils import assert_no_reveal_environment, json_load, validate_blind_config

ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("blind_config.json"))
    p.add_argument("--output", type=Path, default=Path("results/blind_convergence"))
    p.add_argument("--force-python", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    assert_no_reveal_environment()
    cfg = json_load(args.config)
    validate_blind_config(cfg)
    res = [str(v) for v in cfg["numerics"]["hopf_resolutions"]]
    env = os.environ.copy()
    env["SST_HOPF_FORCE_PYTHON"] = "1" if args.force_python else "0"
    cmd = [
        sys.executable, "run_director_convergence.py",
        "--output", str(args.output),
        "--resolutions", *res,
        "--extent", str(cfg["numerics"]["hopf_extent"]),
        "--fiber-samples", str(cfg["numerics"]["fiber_samples"]),
    ]
    print(">>", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
