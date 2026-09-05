#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.core import (
    run_all_checks,
)


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Full SST chiral Kelvin "
            "falsification battery."
        )
    )

    parser.add_argument(
        "--out-dir",
        default="audit_out",
    )

    parser.add_argument(
        "--force-python",
        action="store_true",
    )

    parser.add_argument(
        "--force-build",
        action="store_true",
    )

    args = parser.parse_args()

    summary = run_all_checks(
        out_dir=args.out_dir,
        force_python=args.force_python,
        force_build=args.force_build,
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    return (
        0
        if summary["ok"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
