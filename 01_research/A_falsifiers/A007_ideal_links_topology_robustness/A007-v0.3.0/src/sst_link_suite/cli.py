from __future__ import annotations
import argparse, json, os
from pathlib import Path
from .campaign import run_campaign, rebuild_campaign_outputs
from .parser import parse_ideal_links
from .ridgerunner import export_links
from .native_ext import BackendOptions
from .native_ext.build_ext_if_needed import build_if_needed, extension_path, source_hash


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
    r.add_argument("--require-native", action="store_true")
    r.add_argument("--force-python", action="store_true")
    r.add_argument("--skip-native-build", action="store_true")
    r.add_argument("--force-native-build", action="store_true")
    r.add_argument("--build-verbose", action="store_true")
    r.add_argument("--native-threads", type=int, default=None)
    r.add_argument("--skip-parity", action="store_true")
    r.add_argument("--defer-report", action="store_true")

    rr = sub.add_parser("rebuild-report")
    rr.add_argument("--input", required=True)
    rr.add_argument("--output", required=True)
    rr.add_argument("--config", required=True)
    rr.add_argument("--ids", nargs="*")
    rr.add_argument("--all-database", action="store_true")

    l = sub.add_parser("list")
    l.add_argument("--input", required=True)
    b = sub.add_parser("build-native")
    b.add_argument("--force", action="store_true")
    b.add_argument("--strict", action="store_true")
    b.add_argument("--verbose", action="store_true")
    e = sub.add_parser("export-ridgerunner")
    e.add_argument("--input", required=True)
    e.add_argument("--output", required=True)
    e.add_argument("--sample-n", type=int, default=1024)
    e.add_argument("--ids", nargs="*")
    e.add_argument("--all-database", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "list":
        links = parse_ideal_links(args.input)
        for key, value in links.items():
            print(f"{key}\tcomponents={len(value.components)}\tConway={value.conway}")
        return 0
    if args.command == "build-native":
        ok = build_if_needed(force=args.force, verbose=args.verbose)
        report = {
            "ok": bool(ok),
            "extension_path": str(extension_path()),
            "source_hash": source_hash(),
        }
        print(json.dumps(report, indent=2))
        return 0 if ok else 1
    if args.command == "export-ridgerunner":
        report = export_links(
            args.input, args.output, args.sample_n,
            ids=args.ids or None, all_database=args.all_database,
        )
        print(json.dumps(report, indent=2))
        return 0
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.command == "rebuild-report":
        meta = rebuild_campaign_outputs(
            args.input, args.output, cfg,
            ids=args.ids or None, all_database=args.all_database,
        )
        return 1 if meta["failures"] else 0

    if args.native_threads is not None:
        if args.native_threads < 1:
            raise ValueError("--native-threads must be >= 1")
        os.environ["SST_NATIVE_MAX_THREADS"] = str(args.native_threads)
    options = BackendOptions(
        force_python=args.force_python,
        require_native=args.require_native,
        skip_build=args.skip_native_build,
        force_build=args.force_native_build,
        build_verbose=args.build_verbose,
    )
    meta = run_campaign(
        args.input, args.output, cfg,
        ids=args.ids or None, all_database=args.all_database,
        resume=not args.no_resume, backend_options=options,
        skip_parity=args.skip_parity,
        defer_report=args.defer_report,
    )
    return 1 if meta["failures"] else 0


if __name__ == "__main__":
    import sys
    code = int(main())
    sys.stdout.flush()
    sys.stderr.flush()
    # Some OpenMP runtimes can deadlock during CPython finalization after many native kernels.
    # All campaign files are already closed and fsynced by this point, so use a hard CLI exit.
    os._exit(code)
