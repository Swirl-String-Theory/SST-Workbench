#!/usr/bin/env python3
"""Re-classify KnotPlot knots/*/catalog_status.json without re-running RR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from classify_catalog_status import classify
from run_build_batch import DEFAULT_KNOTS_ROOT, discover_build_ids, parse_ids


def reclassify_one(outdir: Path) -> dict:
    result = classify(outdir)
    out = outdir / "catalog_status.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--knots-root",
        type=Path,
        default=DEFAULT_KNOTS_ROOT,
        help="KnotPlot knots/ root",
    )
    ap.add_argument("--ids", type=str, default=None, help="comma-separated folder ids")
    ap.add_argument("--all", action="store_true", help="all discoverable build folders")
    ap.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="optional JSON summary path",
    )
    args = ap.parse_args(argv)
    root = args.knots_root.resolve()
    if args.ids:
        ids = parse_ids(args.ids)
    elif args.all:
        ids = discover_build_ids(root)
    else:
        ap.error("need --all or --ids")
        return 2

    rows = []
    for folder_id in ids:
        outdir = root / folder_id
        if not outdir.is_dir():
            rows.append({"id": folder_id, "status": "missing-dir"})
            continue
        try:
            result = reclassify_one(outdir)
            rows.append(
                {
                    "id": folder_id,
                    "status": result.get("status"),
                    "residual": (result.get("primary_metrics") or {}).get("residual"),
                    "primary_polish": result.get("primary_polish"),
                }
            )
            print(f"{folder_id}: {result.get('status')}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            rows.append({"id": folder_id, "status": "error", "error": str(exc)})
            print(f"{folder_id}: ERROR {exc}", file=sys.stderr)

    payload = {"count": len(rows), "results": rows}
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"summary: {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
