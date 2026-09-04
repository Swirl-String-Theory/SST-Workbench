#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.convergence_v012 import (
    DEFAULT_MATCHING_CLUSTER_TOL,
    run_convergence_campaign_v012,
)


PRESETS = {
    "quick": (48, 64, 96),
    "full": (64, 96, 128),
    "max": (128, 192, 256),
    "resolved": (256, 320, 384),
}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "SST chiral Kelvin v0.1.3 "
            "resolution/convergence ladder."
        )
    )

    ap.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="quick",
    )

    ap.add_argument(
        "--resolutions",
        default="",
        help=(
            "Optional explicit override, "
            "e.g. 64,96,128."
        ),
    )

    ap.add_argument(
        "--geometries",
        default="ring,trefoil",
    )

    ap.add_argument(
        "--matching-cluster-tol",
        type=float,
        default=DEFAULT_MATCHING_CLUSTER_TOL,
    )

    ap.add_argument(
        "--core-factor",
        type=float,
        default=1.0,
    )

    ap.add_argument(
        "--out-dir",
        default="audit_out_v0121/convergence",
    )

    ap.add_argument(
        "--force-python",
        action="store_true",
    )

    ap.add_argument(
        "--force-build",
        action="store_true",
    )

    ap.add_argument(
        "--require-numerical-tracking",
        action="store_true",
    )

    ap.add_argument(
        "--require-physical-ready",
        action="store_true",
    )

    args = ap.parse_args()

    if args.resolutions:
        resolutions = tuple(
            int(value.strip())
            for value
            in args.resolutions.split(",")
            if value.strip()
        )
    else:
        resolutions = PRESETS[
            args.preset
        ]

    geometries = tuple(
        value.strip()
        for value
        in args.geometries.split(",")
        if value.strip()
    )

    result = run_convergence_campaign_v012(
        out_dir=args.out_dir,
        resolutions=resolutions,
        geometries=geometries,
        core_factor=args.core_factor,
        matching_cluster_tol=
            args.matching_cluster_tol,
        force_python=args.force_python,
        force_build=args.force_build,
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
    raise SystemExit(main())
