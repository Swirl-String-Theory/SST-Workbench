from __future__ import annotations

import argparse
from pathlib import Path

from .campaign import run_campaign, save_campaign


def main() -> int:
    parser = argparse.ArgumentParser(prog="sst-maxwell-falsify")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="Run one preregistered campaign")
    run.add_argument("--config", required=True, type=Path)
    run.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.cmd == "run":
        result = run_campaign(args.config)
        save_campaign(result, args.out)
        print(result["overall_verdict"])
        print(args.out / "report.md")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
