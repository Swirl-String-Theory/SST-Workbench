#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.convergence import (
    run_convergence_campaign,
)


def parse_ints(
    value: str,
) -> tuple[int, ...]:

    return tuple(
        int(item.strip())
        for item
        in value.split(",")
        if item.strip()
    )


def parse_strings(
    value: str,
) -> tuple[str, ...]:

    return tuple(
        item.strip()
        for item
        in value.split(",")
        if item.strip()
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "SST chiral Kelvin v0.1.1 "
            "mode matching and convergence."
        )
    )

    parser.add_argument(
        "--resolutions",
        default="24,32,48,64",
        help="Comma-separated N values.",
    )

    parser.add_argument(
        "--geometries",
        default="ring,trefoil",
        help=(
            "Comma-separated geometries: "
            "ring,trefoil"
        ),
    )

    parser.add_argument(
        "--core-factor",
        type=float,
        default=1.0,
        help="a/r_c",
    )

    parser.add_argument(
        "--out-dir",
        default="audit_out/convergence",
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
        "--require-converged",
        action="store_true",
        help=(
            "Exit 1 when highest-resolution "
            "pairs are not interpretation-ready."
        ),
    )

    args = parser.parse_args()

    summary = run_convergence_campaign(
        out_dir=args.out_dir,
        resolutions=parse_ints(
            args.resolutions
        ),
        geometries=parse_strings(
            args.geometries
        ),
        core_factor=args.core_factor,
        force_python=args.force_python,
        force_build=args.force_build,
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    if (
        args.require_converged
        and
        not summary[
            "physical_interpretation_ready"
        ]
    ):
        return 1

    return (
        0
        if summary[
            "matcher_self_check"
        ]["ok"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
