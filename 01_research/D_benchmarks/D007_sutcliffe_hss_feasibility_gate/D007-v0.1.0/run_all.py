#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from nonlocal_circle import validate
from identifiability import run as run_identifiability
from sector_seeds import main as write_seeds


def main() -> None:
    outputs = ROOT / "outputs"
    outputs.mkdir(exist_ok=True)

    circle = validate()
    (outputs / "circle_validation.json").write_text(
        json.dumps(circle.as_dict(), indent=2), encoding="utf-8"
    )
    if circle.relative_error > 1e-10:
        raise RuntimeError("analytic circle formula failed quadrature validation")

    ident = run_identifiability()
    (outputs / "identifiability.json").write_text(
        json.dumps(ident.as_dict(), indent=2), encoding="utf-8"
    )

    write_seeds(str(outputs / "seeds"))

    summary = {
        "circle_formula_validated": True,
        "circle_relative_error": circle.relative_error,
        "energy_only_rank": ident.energy_only_rank,
        "energy_plus_length_rank": ident.energy_length_rank,
        "jacobian_condition_number": ident.condition_number,
        "sector_seed_generation": True,
        "public_geometry_gate": "partial fail: only axial Q=1,2 analytic",
    }
    (outputs / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
