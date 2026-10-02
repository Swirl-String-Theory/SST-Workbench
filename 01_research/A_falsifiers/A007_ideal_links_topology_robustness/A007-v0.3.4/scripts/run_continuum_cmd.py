#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def flatten_ids(values):
    if not values:
        return ["L2a1", "L4a1", "L6a4", "L6n1", "L7n2"]
    out = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Windows-CMD friendly v0.3.4.1 continuum launcher."
    )
    ap.add_argument("--preset", "-Preset", choices=["quick", "full", "max"], default="full")
    ap.add_argument("--ids", "-Ids", nargs="*", default=None)
    ap.add_argument("--output", "-Output", default=None)
    ap.add_argument("--all-database", "-AllDatabase", action="store_true")
    ap.add_argument("--force-native-build", "-ForceNativeBuild", action="store_true")
    ap.add_argument("--build-verbose", "-BuildVerbose", action="store_true")
    args = ap.parse_args()

    output = args.output or f"outputs_continuum_{args.preset}"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_continuum.py"),
        "--config", str(ROOT / "configs" / f"qm_{args.preset}.json"),
        "--output", str(ROOT / output) if not Path(output).is_absolute() else output,
        "--require-native",
        "--skip-native-build",
    ]

    if args.all_database:
        command.append("--all-database")
        command += ["--ids"]
    else:
        command += ["--ids", *flatten_ids(args.ids)]

    if args.build_verbose:
        command.append("--build-verbose")

    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
