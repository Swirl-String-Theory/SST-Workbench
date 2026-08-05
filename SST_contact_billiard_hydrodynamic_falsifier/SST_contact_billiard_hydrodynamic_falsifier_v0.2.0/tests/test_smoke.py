from pathlib import Path

from sstcbhf.campaign import analyze_curve
from sstcbhf.io import torus_trefoil


def test_negative_control_smoke(tmp_path: Path):
    points = torus_trefoil(512)
    summary = analyze_curve(
        points,
        tmp_path / "demo",
        source={"kind": "test_negative_control"},
        samples=48,
        hydro_samples=16,
        core_ratios=[0.2],
        hydro_interactions=["full", "nonlocal"],
    )
    assert (tmp_path / "demo" / "summary.json").exists()
    assert len(summary["gates"]) == 9
    assert summary["scientific_verdict"] in {
        "FALSIFIED_OR_UNRESOLVED_AT_ONE_OR_MORE_GATES",
        "INCOMPLETE_REQUIRED_GATES_NOT_RUN",
        "NOT_FALSIFIED_BY_CONFIGURED_GATES",
    }
