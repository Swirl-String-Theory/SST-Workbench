from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext.knot_catalog import DEFAULT_KNOT_IDS, available_knots, centerline_summary, sample_ideal_knot


def main() -> int:
    assert available_knots() == DEFAULT_KNOT_IDS
    for knot_id in DEFAULT_KNOT_IDS:
        curve = sample_ideal_knot(knot_id, 1024)
        summary = centerline_summary(curve, knot_id)
        assert curve.shape == (1024, 3)
        assert summary["edge_length_cv"] < 5e-4
        assert summary["source_length_relative_error"] < 2e-4
    print("catalog tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
