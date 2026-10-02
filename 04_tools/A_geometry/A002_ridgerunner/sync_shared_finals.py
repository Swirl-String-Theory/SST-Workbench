#!/usr/bin/env python3
"""
Backfill KnotPlot/knots/final/{id}_final.* from historical finals next to each .kpc.

Examples:
  sync_shared_finals.cmd
  sync_shared_finals.cmd --kind knot
  sync_shared_finals.cmd --ids knot_3.1,torus_6.9 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from run_build_batch import (
    DEFAULT_KNOTS_ROOT,
    discover_build_ids,
    parse_ids,
    parse_kinds,
)
from write_final_snapshot import (
    DEFAULT_SHARED_FINALS,
    load_rop,
    mirror_final_to_shared,
)

BUNDLE = Path(__file__).resolve().parent


def list_historical_finals(folder: Path) -> list[Path]:
    """build_*_final_*.txt in folder (exclude shared-style {id}_final.txt and uniforms)."""
    out: list[Path] = []
    for p in sorted(folder.glob("*_final_*.txt")):
        lower = p.name.lower()
        if "uniform" in lower:
            continue
        # Skip accidental copies that look like shared stem without timestamp
        # Shared names are {id}_final.txt — no second "_final_" middle segment with stamp
        # Historical: build_knot_3.1_final_min_20260812_100000.txt
        if "_final_" not in p.stem:
            continue
        out.append(p)
    return out


def pick_best_final_in_folder(folder: Path) -> tuple[Path, float | None, dict[str, Any]]:
    """Lowest Rop among historical finals; else newest mtime."""
    finals = list_historical_finals(folder)
    if not finals:
        raise FileNotFoundError(f"no historical final in {folder}")

    scored: list[tuple[float, float, Path]] = []
    for p in finals:
        met = Path(str(p).removesuffix(".txt") + ".metrics.json")
        rop = load_rop(met)
        key_rop = rop if rop is not None else float("inf")
        # Prefer newer when Rop missing/tied
        mtime = -p.stat().st_mtime
        scored.append((key_rop, mtime, p))
    scored.sort()
    best = scored[0][2]
    met = Path(str(best).removesuffix(".txt") + ".metrics.json")
    rop = load_rop(met)
    pick = "lowest_rop" if scored[0][0] != float("inf") else "newest_mtime"
    return best, rop, {"pick": pick, "candidates": len(finals)}


def sync_one(
    folder: Path,
    *,
    shared_dir: Path,
    dry_run: bool,
) -> dict[str, Any]:
    build_id = folder.name
    try:
        final_txt, rop, info = pick_best_final_in_folder(folder)
    except FileNotFoundError:
        return {
            "id": build_id,
            "status": "skipped",
            "reason": "no final",
        }
    if dry_run:
        return {
            "id": build_id,
            "status": "dry-run",
            "source": str(final_txt),
            "rop": rop,
            "dest": str(shared_dir / f"{build_id}_final.txt"),
            "pick": info.get("pick"),
        }
    try:
        written = mirror_final_to_shared(
            final_txt, build_id=build_id, shared_dir=shared_dir
        )
    except (OSError, ValueError, FileNotFoundError) as exc:
        return {
            "id": build_id,
            "status": "failed",
            "error": str(exc),
            "source": str(final_txt),
        }
    return {
        "id": build_id,
        "status": "ok",
        "source": str(final_txt),
        "shared_txt": str(written["txt"]),
        "rop": rop,
        "pick": info.get("pick"),
    }


def try_sync_shared_finals(
    *,
    knots_root: Path | None = None,
    shared_dir: Path | None = None,
    ids: list[str] | None = None,
    kinds: set[str] | None = None,
) -> dict[str, Any] | None:
    """Best-effort sync for outer drivers; WARNING and None on hard failure."""
    try:
        result = sync_shared_finals(
            knots_root=knots_root,
            shared_dir=shared_dir,
            ids=ids,
            kinds=kinds,
            dry_run=False,
        )
        print(
            f"Shared finals sync: ok={result['ok']} skipped={result['skipped']} "
            f"failed={result['failures']} -> {result['shared_dir']}",
            flush=True,
        )
        return result
    except (OSError, ValueError) as exc:
        print(f"WARNING: shared finals sync failed: {exc}", flush=True)
        return None


def sync_shared_finals(
    *,
    knots_root: Path | None = None,
    shared_dir: Path | None = None,
    ids: list[str] | None = None,
    kinds: set[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    knots_root = (knots_root or DEFAULT_KNOTS_ROOT).resolve()
    shared = (shared_dir or (knots_root / "final")).resolve()
    if ids is None:
        ids = discover_build_ids(knots_root, kinds=kinds)

    results: list[dict[str, Any]] = []
    failures = 0
    skipped = 0
    ok = 0
    for build_id in ids:
        folder = knots_root / build_id
        if not folder.is_dir():
            row = {"id": build_id, "status": "skipped", "reason": "missing folder"}
            results.append(row)
            skipped += 1
            continue
        row = sync_one(folder, shared_dir=shared, dry_run=dry_run)
        results.append(row)
        st = row["status"]
        if st == "ok" or st == "dry-run":
            ok += 1
        elif st == "skipped":
            skipped += 1
        else:
            failures += 1

    return {
        "status": "ok" if failures == 0 else "failed",
        "knots_root": str(knots_root),
        "shared_dir": str(shared),
        "count": len(ids),
        "ok": ok,
        "skipped": skipped,
        "failures": failures,
        "dry_run": dry_run,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Copy best historical build_*_final_* per knots/<id> into "
            "knots/final/{id}_final.txt (overwrite)"
        )
    )
    ap.add_argument(
        "--knots-root",
        type=Path,
        default=None,
        help=f"default: {DEFAULT_KNOTS_ROOT}",
    )
    ap.add_argument(
        "--shared-dir",
        type=Path,
        default=None,
        help=f"default: <knots-root>/final (or {DEFAULT_SHARED_FINALS})",
    )
    ap.add_argument("--kind", default=None, help="filter: knot,link,torus,tlink")
    ap.add_argument("--ids", default=None, help="comma-separated folder ids")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    try:
        ids = parse_ids(args.ids) if args.ids else None
        kinds = parse_kinds(args.kind) if args.kind else None
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    knots_root = (args.knots_root or DEFAULT_KNOTS_ROOT).resolve()
    if ids is None and not discover_build_ids(knots_root, kinds=kinds):
        print(f"error: no build folders under {knots_root}", file=sys.stderr)
        return 1

    result = sync_shared_finals(
        knots_root=knots_root,
        shared_dir=args.shared_dir,
        ids=ids,
        kinds=kinds,
        dry_run=args.dry_run,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))
    for row in result["results"]:
        st = row["status"]
        if st == "ok":
            print(f"  {row['id']}: {row['shared_txt']}")
        elif st == "dry-run":
            print(f"  {row['id']}: DRY {row['source']} -> {row['dest']}")
        elif st == "skipped":
            print(f"  {row['id']}: skipped ({row.get('reason')})")
        else:
            print(f"  {row['id']}: FAILED {row.get('error')}")
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
