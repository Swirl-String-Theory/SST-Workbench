from __future__ import annotations
import argparse, json
from pathlib import Path
from .blind import run_blind
from .freeze import freeze
from .unblind import unblind
from .plotting import plot_outdir
from .audit import audit_blindness


def main():
    ap=argparse.ArgumentParser(prog="sst-varrow")
    sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("audit"); p.add_argument("--root",default=".")
    p=sp.add_parser("blind"); p.add_argument("campaign"); p.add_argument("outdir"); p.add_argument("--config",default="config/default.json")
    p=sp.add_parser("freeze"); p.add_argument("outdir")
    p=sp.add_parser("plot"); p.add_argument("outdir")
    p=sp.add_parser("unblind"); p.add_argument("outdir"); p.add_argument("--target",default="sealed/unblind_target.json"); p.add_argument("--config",default="config/default.json")
    a=ap.parse_args()
    if a.cmd=="audit":
        hits=audit_blindness(a.root); print(json.dumps({"ok":not hits,"hits":hits},indent=2)); raise SystemExit(1 if hits else 0)
    if a.cmd=="blind": print(json.dumps(run_blind(a.campaign,a.outdir,a.config),indent=2))
    elif a.cmd=="freeze": print(json.dumps(freeze(a.outdir),indent=2))
    elif a.cmd=="plot": plot_outdir(a.outdir)
    elif a.cmd=="unblind": print(json.dumps(unblind(a.outdir,a.target,a.config),indent=2))
