from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "analyze_iso_gamma_area", ROOT / "tools" / "analyze_iso_gamma_area.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def row(run_id: str, family: str, q: float, certified: bool = True) -> dict[str, str]:
    return {
        "run_id": run_id,
        "family_id": family,
        "representation": "continuum",
        "radius_ratio_to_hole": "0.5",
        "gamma_over_area": "32",
        "predicted_period": "0.392699",
        "t_dyn": "0.392699",
        "q_gamma_signed": str(q),
        "q_gamma_stderr": "0.001",
        "t_dyn_certified": str(certified),
        "t_dyn_certification_reason": "PASS" if certified else "FAIL",
    }


def test_analyzer_passes_unit_q_family() -> None:
    result = mod.analyze(
        [row("a", "f", 0.995), row("b", "f", 1.005)],
        q_tolerance=0.02,
        spread_tolerance=0.02,
    )
    assert result["overall_verdict"] == "PASS_WITHIN_FROZEN_BUNDLE_MODEL"


def test_analyzer_falsifies_certified_nonunit_q() -> None:
    result = mod.analyze(
        [row("a", "f", 0.1), row("b", "f", 0.2)],
        q_tolerance=0.02,
        spread_tolerance=0.02,
    )
    assert result["overall_verdict"] == "FALSIFIED_WITHIN_FROZEN_BUNDLE_MODEL"
    assert result["run_falsifications"] == 2
