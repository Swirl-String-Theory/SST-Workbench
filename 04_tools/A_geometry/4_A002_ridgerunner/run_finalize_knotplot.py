#!/usr/bin/env python3
"""
Scan KnotPlot/knots and write build_*_final_* snapshots next to each .kpc.

Does not re-run KnotPlot or Ridgerunner.

Examples:
  run_finalize_knotplot.cmd
  run_finalize_knotplot.cmd --effort min
  run_finalize_knotplot.cmd --kind knot,link,torus --suffix backlog
  run_finalize_knotplot.cmd --ids knot_3.1,torus_6.9 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from run_build_batch import (
    DEFAULT_KNOTS_ROOT,
    discover_build_ids,
    parse_ids,
    parse_kinds,
)
from run_catalog_batch import write_summary
from sync_shared_finals import try_sync_shared_finals
from upsert_polish_to_catalog import try_upsert_polish_to_catalog
from write_final_snapshot import (
    BUNDLE,
    infer_build_stem,
    pick_best_polish_in_folder,
    write_final_snapshot,
)

DEFAULT_SUMMARY = BUNDLE / "out" / "finalize_knotplot_summary.json"


def finalize_one(
    folder: Path,
    *,
    tag: str,
    suffix: str | None,
    dry_run: bool,
    catalog_upsert: bool = True,
) -> dict:
    build_id = folder.name
    stem = infer_build_stem(folder)
    if not stem:
        return {
            "id": build_id,
            "status": "skipped",
            "reason": "no build_*.kpc",
        }
    try:
        polish, rop, info = pick_best_polish_in_folder(folder)
    except FileNotFoundError:
        return {
            "id": build_id,
            "status": "skipped",
            "reason": "no polish",
            "stem": stem,
        }

    planned = f"{stem}_final_{tag}" + (f"_{suffix}" if suffix else "") + "_<timestamp>.txt"
    if dry_run:
        return {
            "id": build_id,
            "status": "dry-run",
            "stem": stem,
            "tag": tag,
            "polish": str(polish),
            "rop": rop,
            "dest": str(folder),
            "planned": planned,
            "pick": info.get("pick"),
        }

    try:
        written = write_final_snapshot(
            polish,
            stem=stem,
            tag=tag,
            dest=folder,
            suffix=suffix,
            extra_alias={
                "rop": rop,
                "pick": info.get("pick"),
                "source": "run_finalize_knotplot",
            },
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        return {
            "id": build_id,
            "status": "failed",
            "stem": stem,
            "error": str(exc),
            "polish": str(polish),
        }

    catalog = None
    if catalog_upsert:
        # KnotPlot knots/ only: resample this polish → uniform N300 → JS
        catalog = try_upsert_polish_to_catalog(
            polish,
            folder,
            final_txt=written["txt"],
        )

    return {
        "id": build_id,
        "status": "ok",
        "stem": stem,
        "tag": tag,
        "polish": str(polish),
        "rop": rop,
        "final_txt": str(written["txt"]),
        "final_alias": str(written["alias"]),
        "pick": info.get("pick"),
        "catalog_upsert": bool(catalog),
        "catalog_uniform": (catalog or {}).get("uniform") if catalog else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Scan KnotPlot/knots for Ridgerunner polish and write "
            "build_*_final_* snapshots next to each build_*.kpc"
        )
    )
    ap.add_argument(
        "--knots-root",
        type=Path,
        default=None,
        help=f"default: {DEFAULT_KNOTS_ROOT}",
    )
    ap.add_argument(
        "--kind",
        default=None,
        help="filter: knot,link,torus,tlink",
    )
    ap.add_argument(
        "--ids",
        default=None,
        help="comma-separated folder ids (default: discover all with build_*.kpc)",
    )
    ap.add_argument(
        "--effort",
        default=None,
        help="use as --tag (min|normal|extra); default tag is finalize",
    )
    ap.add_argument(
        "--tag",
        default=None,
        help="final tag segment (overrides --effort; default: finalize)",
    )
    ap.add_argument("--suffix", default=None, help="optional name suffix")
    ap.add_argument(
        "--catalog-upsert",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "after snapshot: resample polish → uniform N300 and upsert "
            "knotplot_knots_data.js (default: on; --no-catalog-upsert to skip)"
        ),
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fail-fast", action="store_true")
    ap.add_argument(
        "--summary",
        type=Path,
        default=None,
        help=f"default: {DEFAULT_SUMMARY}",
    )
    args = ap.parse_args(argv)

    knots_root = (args.knots_root or DEFAULT_KNOTS_ROOT).resolve()
    tag = args.tag or args.effort or "finalize"

    try:
        if args.ids:
            ids = parse_ids(args.ids)
        else:
            kinds = parse_kinds(args.kind) if args.kind else None
            ids = discover_build_ids(knots_root, kinds=kinds)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not ids:
        print(f"error: no folders to finalize under {knots_root}", file=sys.stderr)
        return 1

    summary_path = args.summary or DEFAULT_SUMMARY
    print("============================================================")
    print(f"run_finalize_knotplot  ids={len(ids)}  tag={tag}")
    print(f"knots-root: {knots_root}")
    print(f"summary:    {summary_path}")
    if args.suffix:
        print(f"suffix:     {args.suffix}")
    print(f"catalog:    {'on' if args.catalog_upsert and not args.dry_run else 'off'}")
    if args.dry_run:
        print("dry-run:    on")
    print("============================================================")

    t0 = time.perf_counter()
    results: list[dict] = []
    failures = 0
    skipped = 0
    for i, build_id in enumerate(ids, start=1):
        folder = knots_root / build_id
        print(f"[{i}/{len(ids)}] {build_id}", flush=True)
        if not folder.is_dir():
            row = {"id": build_id, "status": "skipped", "reason": "missing folder"}
            results.append(row)
            skipped += 1
            print(f"  -> skipped (missing folder)", flush=True)
            continue
        row = finalize_one(
            folder,
            tag=tag,
            suffix=args.suffix,
            dry_run=args.dry_run,
            catalog_upsert=bool(args.catalog_upsert) and not args.dry_run,
        )
        results.append(row)
        status = row["status"]
        if status == "ok":
            print(f"  -> {row['final_txt']}", flush=True)
        elif status == "dry-run":
            print(f"  -> DRY {row.get('polish')} -> {row.get('planned')}", flush=True)
        elif status == "skipped":
            skipped += 1
            print(f"  -> skipped ({row.get('reason')})", flush=True)
        else:
            failures += 1
            print(f"  -> FAILED {row.get('error')}", flush=True)
            if args.fail_fast:
                break

    elapsed = time.perf_counter() - t0
    overall = "ok" if failures == 0 else "failed"
    if args.dry_run and failures == 0:
        overall = "dry-run"
    payload = {
        "status": overall,
        "tag": tag,
        "suffix": args.suffix,
        "knots_root": str(knots_root),
        "count": len(ids),
        "failures": failures,
        "skipped": skipped,
        "elapsed_s": elapsed,
        "results": results,
    }
    write_summary(summary_path, payload)
    print()
    print(
        f"Done: {overall}  ok/dry={len(ids) - failures - skipped}  "
        f"skipped={skipped}  failures={failures}"
    )
    print(f"Summary: {summary_path}")

    if not args.dry_run:
        # Safety-net: ensure knots/final has current best for processed ids
        try_sync_shared_finals(knots_root=knots_root, ids=ids)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
