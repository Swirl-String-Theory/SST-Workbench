#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDS = ["L2a1", "L4a1", "L6a4", "L6n1", "L7n2"]


def flatten_ids(values):
    if values is None:
        return list(DEFAULT_IDS)
    out = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Windows-CMD friendly spectral audit launcher.")
    ap.add_argument("--ids", "-Ids", nargs="*", default=None)
    ap.add_argument("--output", "-Output", default="outputs_spectral")
    ap.add_argument("--all-database", "-AllDatabase", action="store_true")
    args = ap.parse_args()

    command = [
        sys.executable, str(ROOT / "scripts" / "run_spectral.py"),
        "--config", str(ROOT / "configs" / "spectral_audit.json"),
        "--output", args.output,
    ]
    if args.all_database:
        command.append("--all-database")
        command += ["--ids"]
    else:
        command += ["--ids", *flatten_ids(args.ids)]
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
