from __future__ import annotations
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sst_finite_core_falsifier.mega_campaign import run_mega


def main():
    ap = argparse.ArgumentParser(description="A029 v0.7.0 Specific-Lagrangian Mega Falsifier")
    ap.add_argument("--config", default="config/preset_specific_lagrangian_mega_v070.json")
    ap.add_argument("--out", default="A029-v0.7.0-outputs")
    ap.add_argument("--limit", type=int, default=None, help="Diagnostic only; any limit makes the run non-certifying.")
    ap.add_argument("--diagnostic-python", action="store_true", help="Allow Python fallback; never production certification.")
    ap.add_argument("--no-reveal", action="store_true")
    a = ap.parse_args()
    r = run_mega(
        ROOT,
        ROOT / a.config,
        ROOT / a.out,
        limit=a.limit,
        diagnostic_python=a.diagnostic_python,
        do_reveal=not a.no_reveal,
    )
    print(json.dumps(r["pipeline"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
