#!/usr/bin/env python3
"""Operational Fase-B re-run queues for KnotPlot build corrections."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from run_build_batch import DEFAULT_KNOTS_ROOT, discover_build_ids, main as batch_main

UNFINISHED = ["link_6.3.3", "link_7.2.5", "torus_2.6"]
CONTINUE = ["knot_5.1", "knot_5.2", "knot_6.1", "torus_3.3"]
STATUS_ONLY = ["link_4.2.1"]
SKIP_RR = {"knot_0.1"}


def legacy_link_ids(knots_root: Path) -> list[str]:
    ids = discover_build_ids(knots_root, kinds={"link"})
    # Prefer stalled / unfinished-looking links; always exclude skip set.
    out: list[str] = []
    for folder_id in ids:
        if folder_id in SKIP_RR:
            continue
        status_path = knots_root / folder_id / "catalog_status.json"
        status = None
        if status_path.is_file():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8")).get(
                    "status"
                )
            except (OSError, json.JSONDecodeError):
                status = None
        if status in (
            None,
            "stalled-not-converged",
            "relaxed-seed",
        ) or folder_id in UNFINISHED:
            out.append(folder_id)
    return out


def resolve_queue(name: str, knots_root: Path) -> list[str]:
    key = name.strip().lower()
    if key == "unfinished":
        return list(UNFINISHED)
    if key == "continue":
        return list(CONTINUE)
    if key in ("legacy-links", "legacy_links", "links"):
        return legacy_link_ids(knots_root)
    if key in ("status-only", "status_only"):
        return list(STATUS_ONLY)
    if key == "all":
        ids = []
        for part in (UNFINISHED, CONTINUE, legacy_link_ids(knots_root)):
            for i in part:
                if i not in ids and i not in SKIP_RR:
                    ids.append(i)
        return ids
    raise ValueError(f"unknown queue {name!r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--queue",
        default="unfinished,continue",
        help="comma-separated: unfinished,continue,legacy-links,status-only,all",
    )
    ap.add_argument("--effort", default="normal")
    ap.add_argument("-t", "--threads", type=int, default=8)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--status-only",
        action="store_true",
        help="only reclassify (+ optional upsert resample), no RR",
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=Path(__file__).resolve().parent / "out" / "correction_queue_summary.json",
    )
    args = ap.parse_args(argv)

    knots_root = DEFAULT_KNOTS_ROOT
    ids: list[str] = []
    for part in args.queue.split(","):
        part = part.strip()
        if not part:
            continue
        for folder_id in resolve_queue(part, knots_root):
            if folder_id in SKIP_RR:
                continue
            if folder_id not in ids:
                ids.append(folder_id)

    if not ids:
        print("no ids in selected queues", file=sys.stderr)
        return 1

    print(f"queue ids ({len(ids)}): {','.join(ids)}")
    if args.status_only or "status-only" in {
        p.strip().lower() for p in args.queue.split(",")
    }:
        from reclassify_catalog_status import main as reclassify_main

        return reclassify_main(
            [
                "--ids",
                ",".join(ids),
                "--summary",
                str(args.summary),
            ]
        )

    batch_argv = [
        "--ids",
        ",".join(ids),
        "-rr",
        "--effort",
        args.effort,
        "-t",
        str(args.threads),
        "--jobs",
        str(args.jobs),
        "--summary",
        str(args.summary),
    ]
    if args.dry_run:
        batch_argv.append("--dry-run")
    return batch_main(batch_argv)


if __name__ == "__main__":
    raise SystemExit(main())
