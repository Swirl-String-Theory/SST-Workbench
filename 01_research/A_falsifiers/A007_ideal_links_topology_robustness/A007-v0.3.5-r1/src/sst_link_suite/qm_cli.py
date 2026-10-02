from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .native_ext import BackendOptions
from .qm_campaign import run_qm_campaign, rebuild_qm_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="QM-readiness campaign for ideal vortex links.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--all-database", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--rebuild-only", action="store_true")
    parser.add_argument("--require-native", action="store_true")
    parser.add_argument("--force-python", action="store_true")
    parser.add_argument("--skip-native-build", action="store_true")
    parser.add_argument("--force-native-build", action="store_true")
    parser.add_argument("--build-verbose", action="store_true")
    parser.add_argument("--native-threads", type=int, default=None)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.native_threads is not None:
        if args.native_threads < 1:
            raise ValueError("--native-threads must be >= 1")
        os.environ["SST_NATIVE_MAX_THREADS"] = str(args.native_threads)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if args.rebuild_only:
        metadata = rebuild_qm_outputs(
            args.input, args.output, cfg,
            ids=args.ids or None, all_database=args.all_database,
        )
        return 1 if metadata["failures"] else 0
    options = BackendOptions(
        require_native=args.require_native,
        force_python=args.force_python,
        skip_build=args.skip_native_build,
        force_build=args.force_native_build,
        build_verbose=args.build_verbose,
    )
    metadata = run_qm_campaign(
        args.input, args.output, cfg,
        ids=args.ids or None,
        all_database=args.all_database,
        resume=not args.no_resume,
        backend_options=options,
    )
    return 1 if metadata["failures"] else 0


if __name__ == "__main__":
    import sys
    code = int(main())
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
