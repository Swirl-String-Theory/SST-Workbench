#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.core import (
    run_audit,
    write_json,
)


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Run one SST chiral Kelvin "
            "falsification audit."
        )
    )

    parser.add_argument(
        "--geometry",
        choices=[
            "ring",
            "trefoil",
        ],
        default="trefoil",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--core-factor",
        type=float,
        default=1.0,
        help="a/r_c",
    )

    parser.add_argument(
        "--force-python",
        action="store_true",
    )

    parser.add_argument(
        "--force-build",
        action="store_true",
    )

    parser.add_argument(
        "--out",
        default="",
    )

    parser.add_argument(
        "--summary-only",
        action="store_true",
    )

    args = parser.parse_args()

    result = run_audit(
        geometry=args.geometry,
        n=args.n,
        core_factor=args.core_factor,
        force_python=args.force_python,
        force_build=args.force_build,
    )

    if args.out:
        write_json(
            args.out,
            result,
        )

    if args.summary_only:

        status = (
            "PASS"
            if result["ok"]
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"geometry={args.geometry} "
            f"N={args.n} "
            f"a/r_c={args.core_factor}"
        )

    else:

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    return (
        0
        if result["ok"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
