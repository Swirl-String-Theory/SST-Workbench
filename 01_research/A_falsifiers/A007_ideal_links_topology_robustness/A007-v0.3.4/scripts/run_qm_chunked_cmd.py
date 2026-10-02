#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IDS = ["L2a1", "L4a1", "L5a1", "L6a4", "L6n1", "L7n1"]


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
    ap = argparse.ArgumentParser(description="Windows-CMD friendly process-isolated QM launcher.")
    ap.add_argument("--preset", "-Preset", choices=["quick", "full", "max"], default="quick")
    ap.add_argument("--ids", "-Ids", nargs="*", default=None)
    ap.add_argument("--native-threads", "-NativeThreads", type=int, default=16)
    ap.add_argument("--retry", "-Retry", type=int, default=1)
    ap.add_argument("--output", "-Output", default=None)
    ap.add_argument("--all-database", "-AllDatabase", action="store_true")
    ap.add_argument("--no-resume", "-NoResume", action="store_true")
    args = ap.parse_args()

    command = [
        sys.executable, str(ROOT / "scripts" / "run_qm_chunked.py"),
        "--preset", args.preset,
        "--native-threads", str(args.native_threads),
        "--retry", str(args.retry),
    ]
    if args.output:
        command += ["--output", args.output]
    if args.all_database:
        command.append("--all-database")
    else:
        command += ["--ids", *flatten_ids(args.ids)]
    if args.no_resume:
        command.append("--no-resume")
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
