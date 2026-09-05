#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chiral_kelvin.core import (
    run_all_checks as run_v010_checks,
    write_json,
)

from chiral_kelvin.convergence_v012 import (
    DEFAULT_MATCHING_CLUSTER_TOL,
    run_convergence_campaign_v012,
)

from chiral_kelvin.conclusions import (
    write_conclusions_summary,
)


PRESETS = {
    "quick": (48, 64, 96),
    "full": (64, 96, 128),
    "max": (128, 192, 256),
    "resolved": (256, 320, 384),
}


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "SST chiral Kelvin v0.1.3 "
            "full null + convergence battery."
        )
    )

    parser.add_argument(
        "--out-dir",
        default="audit_out_v0121",
    )

    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        default="quick",
    )

    parser.add_argument(
        "--matching-cluster-tol",
        type=float,
        default=DEFAULT_MATCHING_CLUSTER_TOL,
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
        "--strict-tracking",
        action="store_true",
    )

    parser.add_argument(
        "--strict-physical",
        action="store_true",
    )

    args = parser.parse_args()

    out = Path(args.out_dir)

    baseline = run_v010_checks(
        out_dir=out / "baseline",
        force_python=args.force_python,
        force_build=args.force_build,
    )

    convergence = run_convergence_campaign_v012(
        out_dir=out / "convergence_v012",
        resolutions=PRESETS[args.preset],
        matching_cluster_tol=
            args.matching_cluster_tol,
        force_python=args.force_python,
        force_build=False,
    )

    implementation_ok = bool(
        baseline["ok"]
        and
        convergence[
            "matcher_self_check"
        ]["ok"]
    )

    summary = {
        "audit_name":
            (
                "SST chiral Kelvin "
                "falsification v0.1.3"
            ),

        "implementation_ok":
            implementation_ok,

        "numerical_tracking_ready":
            convergence[
                "numerical_tracking_ready"
            ],

        "physical_interpretation_ready":
            convergence[
                "physical_interpretation_ready"
            ],

        "baseline":
            baseline,

        "convergence":
            convergence,

        # Overall software audit status.
        "ok":
            implementation_ok,

        "interpretation_gate":
            (
                "Implementation validity, numerical "
                "trackability, core resolution and "
                "relative-equilibrium validity are "
                "independent gates."
            ),
    }

    write_json(
        out
        / "audit_summary_v0.1.3.json",
        summary,
    )

    conclusions_summary = (
        write_conclusions_summary(
            out
            / "conclusions_summary.json",
            implementation_ok=
                summary[
                    "implementation_ok"
                ],
            numerical_tracking_ready=
                summary[
                    "numerical_tracking_ready"
                ],
            physical_interpretation_ready=
                summary[
                    "physical_interpretation_ready"
                ],
        )
    )

    summary[
        "conclusions_summary"
    ] = conclusions_summary

    # Rewrite final audit summary with the conclusion-ledger
    # metadata included.
    write_json(
        out
        / "audit_summary_v0.1.3.json",
        summary,
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    if not implementation_ok:
        return 1

    if (
        args.strict_tracking
        and
        not summary[
            "numerical_tracking_ready"
        ]
    ):
        return 2

    if (
        args.strict_physical
        and
        not summary[
            "physical_interpretation_ready"
        ]
    ):
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
