from __future__ import annotations
import argparse, json
from pathlib import Path
from .campaign import run_campaign
from .parser import parse_ideal_links, DEFAULT_TARGETS

def build_parser():
    p = argparse.ArgumentParser(description="Comprehensive test suite for Brian Gilbert ideal links.")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--input", required=True)
    r.add_argument("--output", required=True)
    r.add_argument("--config", required=True)
    r.add_argument("--ids", nargs="*")
    r.add_argument("--all-database", action="store_true")
    r.add_argument("--no-resume", action="store_true")
    l = sub.add_parser("list")
    l.add_argument("--input", required=True)
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "list":
        links = parse_ideal_links(args.input)
        for key, value in links.items():
            print(f"{key}\tcomponents={len(value.components)}\tConway={value.conway}")
        return 0
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    meta = run_campaign(
        args.input, args.output, cfg,
        ids=args.ids or None,
        all_database=args.all_database,
        resume=not args.no_resume,
    )
    return 1 if meta["failures"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
