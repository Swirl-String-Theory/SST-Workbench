from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sst_link_suite.cli import main

parser = argparse.ArgumentParser()
parser.add_argument("--preset", choices=["quick", "full", "max"], default="full")
parser.add_argument("--output", default=None)
parser.add_argument("--all-database", action="store_true")
parser.add_argument("--ids", nargs="*")
parser.add_argument("--no-resume", action="store_true")
parser.add_argument("--require-native", action="store_true")
parser.add_argument("--force-python", action="store_true")
parser.add_argument("--skip-build", action="store_true")
parser.add_argument("--force-build", action="store_true")
parser.add_argument("--build-verbose", action="store_true")
args = parser.parse_args()

output = args.output or str(ROOT / f"outputs_{args.preset}")
argv = [
    "run",
    "--input", str(ROOT / "data" / "idealLinks.txt"),
    "--output", output,
    "--config", str(ROOT / "configs" / f"{args.preset}.json"),
]
for flag in (
    "all_database", "no_resume", "require_native", "force_python",
    "skip_build", "force_build", "build_verbose",
):
    if getattr(args, flag):
        argv.append("--" + flag.replace("_", "-"))
if args.ids:
    argv += ["--ids", *args.ids]
raise SystemExit(main(argv))
