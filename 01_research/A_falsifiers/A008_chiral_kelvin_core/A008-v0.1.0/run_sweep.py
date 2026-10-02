#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json

from chiral_kelvin.core import (
    run_audit,
    write_csv,
    write_json,
)


def parse_list(
    value: str,
    cast,
):
    return [
        cast(item.strip())
        for item
        in value.split(",")
        if item.strip()
    ]


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Sweep SST chiral Kelvin "
            "resolution and core scale."
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
        "--n-values",
        default="20,24,32",
    )

    parser.add_argument(
        "--core-factors",
        default="0.5,1.0,2.0",
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
        "--out-json",
        default="sweep.json",
    )

    parser.add_argument(
        "--out-csv",
        default="sweep.csv",
    )

    args = parser.parse_args()

    n_values = parse_list(
        args.n_values,
        int,
    )

    core_factors = parse_list(
        args.core_factors,
        float,
    )

    rows = []

    for n in n_values:

        for core_factor in core_factors:

            result = run_audit(
                geometry=args.geometry,
                n=n,
                core_factor=core_factor,
                force_python=args.force_python,
                force_build=args.force_build,
            )

            rows.append(
                {
                    "geometry":
                        args.geometry,

                    "N":
                        n,

                    "core_factor":
                        core_factor,

                    "fd_rel":
                        result[
                            "finite_difference_jacobian"
                        ][
                            "relative_error"
                        ],

                    "circulation_rel":
                        result[
                            "circulation_reversal"
                        ][
                            "relative_error"
                        ],

                    "energy_rel":
                        result[
                            "four_state_energy"
                        ][
                            "relative_spread"
                        ],

                    "spectrum_T_rel":
                        result[
                            "spectral_symmetry"
                        ][
                            "circulation_spectrum_residual"
                        ],

                    "spectrum_P_rel":
                        result[
                            "spectral_symmetry"
                        ][
                            "parity_spectrum_residual"
                        ],

                    "ok":
                        result["ok"],
                }
            )

    write_json(
        args.out_json,
        rows,
    )

    write_csv(
        args.out_csv,
        rows,
    )

    print(
        json.dumps(
            rows,
            indent=2,
        )
    )

    return (
        0
        if all(
            row["ok"]
            for row in rows
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
