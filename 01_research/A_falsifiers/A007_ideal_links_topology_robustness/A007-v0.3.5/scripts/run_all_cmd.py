#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def flatten_ids(values):
    if not values:
        return []
    out = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Windows-CMD friendly native ideal-link campaign launcher.")
    ap.add_argument("--preset", "-Preset", choices=["quick", "full", "max"], default="full")
    ap.add_argument("--output", "-Output", default=None)
    ap.add_argument("--all-database", "-AllDatabase", action="store_true")
    ap.add_argument("--ids", "-Ids", nargs="*", default=None)
    ap.add_argument("--native-threads", "-NativeThreads", type=int, default=None)
    ap.add_argument("--retries", "-Retries", type=int, default=2)
    ap.add_argument("--no-resume", "-NoResume", action="store_true")
    ap.add_argument("--chunk-size", "-ChunkSize", type=int, default=None)
    ap.add_argument("--chunk-timeout-s", "-ChunkTimeoutS", type=float, default=180.0)
    args = ap.parse_args()

    command = [
        sys.executable, str(ROOT / "scripts" / "run_all.py"),
        "--preset", args.preset,
        "--skip-build",
        "--single-link-retries", str(args.retries),
        "--chunk-timeout-s", str(args.chunk_timeout_s),
    ]
    if args.output:
        command += ["--output", args.output]
    if args.all_database:
        command.append("--all-database")
    ids = flatten_ids(args.ids)
    if ids:
        command += ["--ids", *ids]
    if args.native_threads:
        command += ["--native-threads", str(args.native_threads)]
    if args.no_resume:
        command.append("--no-resume")
    if args.chunk_size:
        command += ["--chunk-size", str(args.chunk_size)]
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
