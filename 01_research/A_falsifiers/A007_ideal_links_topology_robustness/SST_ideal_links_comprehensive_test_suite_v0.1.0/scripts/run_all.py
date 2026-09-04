from __future__ import annotations
import argparse, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from sst_link_suite.cli import main

p = argparse.ArgumentParser()
p.add_argument("--preset", choices=["quick","full","max"], default="full")
p.add_argument("--output", default=None)
p.add_argument("--all-database", action="store_true")
p.add_argument("--ids", nargs="*")
p.add_argument("--no-resume", action="store_true")
args = p.parse_args()

out = args.output or str(ROOT/f"outputs_{args.preset}")
argv = [
    "run",
    "--input", str(ROOT/"data"/"idealLinks.txt"),
    "--output", out,
    "--config", str(ROOT/"configs"/f"{args.preset}.json"),
]
if args.all_database:
    argv.append("--all-database")
if args.ids:
    argv += ["--ids", *args.ids]
if args.no_resume:
    argv.append("--no-resume")
raise SystemExit(main(argv))
