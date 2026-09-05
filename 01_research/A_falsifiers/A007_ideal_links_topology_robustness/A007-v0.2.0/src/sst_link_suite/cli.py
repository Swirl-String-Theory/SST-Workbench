from __future__ import annotations
import argparse
import json
from pathlib import Path

from .campaign import run_campaign
from .parser import parse_ideal_links
from .native_ext import BackendOptions, NativeBackendError
from .native_ext.build_ext_if_needed import build_if_needed


def _add_backend_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--require-native", action="store_true",
                        help="Hard fail unless the pybind11 C++ backend loads and passes parity.")
    parser.add_argument("--force-python", action="store_true",
                        help="Use the NumPy reference backend even if native is available.")
    parser.add_argument("--skip-build", action="store_true",
                        help="Do not auto-build the native extension.")
    parser.add_argument("--force-build", action="store_true",
                        help="Force a source-hash rebuild before running.")
    parser.add_argument("--build-verbose", action="store_true",
                        help="Print compiler command and diagnostics.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comprehensive native-capable test suite for Brian Gilbert ideal links."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--config", required=True)
    run.add_argument("--ids", nargs="*")
    run.add_argument("--all-database", action="store_true")
    run.add_argument("--no-resume", action="store_true")
    _add_backend_flags(run)

    listing = sub.add_parser("list")
    listing.add_argument("--input", required=True)

    build = sub.add_parser("build-native")
    build.add_argument("--force", action="store_true")
    build.add_argument("--quiet", action="store_true")
    build.add_argument("--strict", action="store_true")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "list":
        links = parse_ideal_links(args.input)
        for key, value in links.items():
            print(f"{key}\tcomponents={len(value.components)}\tConway={value.conway}")
        return 0
    if args.command == "build-native":
        ok = build_if_needed(force=args.force, verbose=not args.quiet)
        return 0 if (ok or not args.strict) else 1

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    options = BackendOptions(
        require_native=args.require_native,
        force_python=args.force_python,
        skip_build=args.skip_build,
        force_build=args.force_build,
        build_verbose=args.build_verbose,
    )
    try:
        metadata = run_campaign(
            args.input,
            args.output,
            cfg,
            ids=args.ids or None,
            all_database=args.all_database,
            resume=not args.no_resume,
            backend_options=options,
        )
    except NativeBackendError as exc:
        print(f"NATIVE GATE FAILED: {exc}")
        return 2
    return 1 if metadata["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
