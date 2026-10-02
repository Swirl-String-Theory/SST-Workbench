#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chiral_kelvin.core import (
    run_all_checks as run_baseline,
    write_json,
)

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

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--out-dir",
        default="audit_out_v012",
    )

    parser.add_argument(
        "--preset",
        choices=PRESETS,
        default="quick",
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

    out = Path(
        args.out_dir
    )

    baseline = run_baseline(
        out_dir=
            out / "baseline",
        force_python=
            args.force_python,
        force_build=
            args.force_build,
    )

    convergence = (
        run_convergence_campaign(
            out_dir=
                out
                / "convergence_v012",

            resolutions=
                PRESETS[
                    args.preset
                ],

            force_python=
                args.force_python,
        )
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
                "falsification v0.1.2"
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

        "ok":
            implementation_ok,
    }

    write_json(
        out
        / "audit_summary_v0.1.2.json",
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
