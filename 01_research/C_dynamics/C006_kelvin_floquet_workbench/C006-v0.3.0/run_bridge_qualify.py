"""Qualify P_BS on D_bridge. Never scores A029 PRED_M0-M3."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sst_kelvin_workbench.qualify import forbid_a029_scoring, run_qualification


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "exports" / "p26_bridge"))
    ap.add_argument("--score-a029", action="store_true", help="rejected: D_score is empty")
    args = ap.parse_args()
    if args.score_a029:
        forbid_a029_scoring()
    cert = run_qualification(Path(args.out))
    print(json.dumps({"status": cert["status"], "reason": cert["reason"], "a029_scored": cert["a029_scored"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
