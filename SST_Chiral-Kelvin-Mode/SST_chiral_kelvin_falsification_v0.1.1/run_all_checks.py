#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chiral_kelvin.core import (
    run_all_checks as run_v010_checks,
    write_json,
)

from chiral_kelvin.convergence import (
    run_convergence_campaign,
)


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "SST chiral Kelvin v0.1.1 "
            "full null + convergence battery."
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

    parser.add_argument(
        "--resolutions",
        default="24,32,48,64",
    )

    parser.add_argument(
        "--strict-convergence",
        action="store_true",
    )

    args = parser.parse_args()

    out = Path(args.out_dir)

    resolutions = tuple(
        int(item.strip())
        for item
        in args.resolutions.split(",")
        if item.strip()
    )

    baseline = run_v010_checks(
        out_dir=out / "baseline",
        force_python=args.force_python,
        force_build=args.force_build,
    )

    convergence = (
        run_convergence_campaign(
            out_dir=out / "convergence",
            resolutions=resolutions,
            force_python=args.force_python,
            force_build=False,
        )
    )

    implementation_ok = bool(
        baseline["ok"]
        and
        convergence[
            "matcher_self_check"
        ]["ok"]
    )

    physical_ready = bool(
        convergence[
            "physical_interpretation_ready"
        ]
    )

    summary = {
        "audit_name":
            (
                "SST chiral Kelvin "
                "falsification v0.1.1"
            ),

        "implementation_ok":
            implementation_ok,

        "physical_interpretation_ready":
            physical_ready,

        "baseline":
            baseline,

        "convergence":
            convergence,

        # Overall software audit status.
        "ok":
            implementation_ok,

        "interpretation_gate":
            (
                "A baseline PASS does not imply "
                "mode convergence. Only mode groups "
                "marked physical_interpretation_allowed "
                "may be interpreted."
            ),
    }

    write_json(
        out
        / "audit_summary_v0.1.1.json",
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
        args.strict_convergence
        and
        not physical_ready
    ):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
