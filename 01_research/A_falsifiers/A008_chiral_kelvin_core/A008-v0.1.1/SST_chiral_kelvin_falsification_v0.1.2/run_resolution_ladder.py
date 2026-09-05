#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.convergence import (
    run_convergence_campaign,
)


PRESETS = {
    "quick": (
        48,
        64,
        96,
    ),
    "full": (
        64,
        96,
        128,
    ),
    "max": (
        128,
        192,
        256,
    ),
}


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "SST chiral Kelvin v0.1.2 "
            "resolution ladder."
        )
    )

    parser.add_argument(
        "--preset",
        choices=PRESETS,
        default="quick",
    )

    parser.add_argument(
        "--out-dir",
        default="audit_out_v012",
    )

    parser.add_argument(
        "--geometries",
        default="ring,trefoil",
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
        "--require-numerical-tracking",
        action="store_true",
    )

    parser.add_argument(
        "--require-physical-ready",
        action="store_true",
    )

    args = parser.parse_args()

    geometries = tuple(
        value.strip()
        for value
        in args.geometries.split(",")
        if value.strip()
    )

    result = run_convergence_campaign(
        out_dir=args.out_dir,
        resolutions=
            PRESETS[args.preset],
        geometries=geometries,
        force_python=
            args.force_python,
        force_build=
            args.force_build,
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    if not result[
        "matcher_self_check"
    ]["ok"]:
        return 1

    if (
        args.require_numerical_tracking
        and
        not result[
            "numerical_tracking_ready"
        ]
    ):
        return 2

    if (
        args.require_physical_ready
        and
        not result[
            "physical_interpretation_ready"
        ]
    ):
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
