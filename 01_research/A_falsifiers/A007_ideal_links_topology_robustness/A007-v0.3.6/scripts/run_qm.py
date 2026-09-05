from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sst_link_suite.qm_cli import main

parser = argparse.ArgumentParser()
parser.add_argument("--preset", choices=["quick", "full", "max"], default="quick")
parser.add_argument("--spectral-variant", choices=["raw", "filtered", "raw-resolved"], default="raw")
parser.add_argument("--output", default=None)
parser.add_argument("--ids", nargs="*")
parser.add_argument("--all-database", action="store_true")
parser.add_argument("--require-native", action="store_true")
parser.add_argument("--force-python", action="store_true")
parser.add_argument("--native-threads", type=int, default=None)
parser.add_argument("--skip-native-build", action="store_true")
parser.add_argument("--force-native-build", action="store_true")
parser.add_argument("--build-verbose", action="store_true")
parser.add_argument("--no-resume", action="store_true")
args = parser.parse_args()

if args.spectral_variant == "raw":
    config_name = f"qm_{args.preset}.json"
elif args.spectral_variant == "filtered":
    config_name = f"qm_{args.preset}_spectral_filtered.json"
else:
    config_name = f"qm_{args.preset}_raw_resolved.json"

argv = [
    "--input", str(ROOT / "data" / "idealLinks.txt"),
    "--output", args.output or str(ROOT / f"outputs_qm_{args.preset}_{args.spectral_variant.replace('-', '_')}"),
    "--config", str(ROOT / "configs" / config_name),
]
if args.ids:
    argv += ["--ids", *args.ids]
if args.all_database:
    argv.append("--all-database")
if args.require_native:
    argv.append("--require-native")
if args.force_python:
    argv.append("--force-python")
if args.native_threads is not None:
    argv += ["--native-threads", str(args.native_threads)]
if args.no_resume:
    argv.append("--no-resume")
if args.skip_native_build:
    argv.append("--skip-native-build")
if args.force_native_build:
    argv.append("--force-native-build")
if args.build_verbose:
    argv.append("--build-verbose")
code = int(main(argv))
sys.stdout.flush()
sys.stderr.flush()
os._exit(code)
