from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext import constants
from fermat_ext.core import analyze_profile
from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS
from fermat_ext.knot_scan import rosenhead_reference_regime
from fermat_ext.resolution import resolution_plan


def main() -> int:
    assert constants.ROSENHEAD_HORIZON_THRESHOLD < constants.ROSENHEAD_CRITICAL_THRESHOLD
    expected = math.sqrt(8.0 / 27.0) * constants.BETA_0
    assert abs(constants.ROSENHEAD_CRITICAL_THRESHOLD - expected) < 1e-16

    critical = analyze_profile("rosenhead", 0.0019, 1e-5, 0.05, 8000, force_python=True, auto_build=False)
    blocked = analyze_profile("rosenhead", 0.0020, 1e-5, 0.05, 8000, force_python=True, auto_build=False)
    assert critical["critical_roots"]
    assert not critical["horizon_roots"]
    assert not blocked["critical_roots"]

    assert rosenhead_reference_regime(0.0019)["classification"] == "STRAIGHT_REFERENCE_HORIZON_FREE_CRITICAL_WINDOW"
    assert rosenhead_reference_regime(0.0045)["classification"] == "STRAIGHT_REFERENCE_NO_FERMAT_CRITICAL_RADIUS"

    selected = []
    for knot_id in DEFAULT_KNOT_IDS:
        plan = resolution_plan(knot_id, epsilon=0.0045, target_ds_over_epsilon=1.0, max_points=8192)
        selected.append(plan["selected_points"])
        assert plan["selected_points"] >= 128
    assert selected == sorted(selected)
    print("v0.3 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
