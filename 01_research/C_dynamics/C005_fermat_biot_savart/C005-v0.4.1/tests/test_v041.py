from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fermat_ext.certification import build_bifurcation_atlas, scan_stationary_candidates
from fermat_ext.resolution import resolution_plan


def main() -> int:
    atlas = scan_stationary_candidates(
        "0_1",
        epsilon=0.0019,
        centerline_points=2048,
        stations=1,
        angles=3,
        rho_min=0.0005,
        rho_max=0.01,
        bracket_samples=64,
        force_python=True,
        auto_build=False,
        reach_pair_points=256,
    )
    assert 0.0 <= atlas["candidate_surface_fraction"] <= 1.0
    assert atlas["candidate_surface_fraction"] == atlas["candidate_surface_fraction_all_rays"]
    conditional = atlas["candidate_surface_fraction_fully_clock_valid_rays"]
    assert conditional is None or 0.0 <= conditional <= 1.0
    assert all(root["classification"] != "CERTIFIED_LOCAL_MINIMUM_NUMERICAL" for root in atlas["roots"])
    assert any(root["classification"] == "RESOLVED_LOCAL_MINIMUM" for root in atlas["roots"])

    plan_scale_1 = resolution_plan(
        "5_2", epsilon=0.0019, scale_over_rc=1.0,
        target_ds_over_epsilon=1.0, min_points=4096, max_points=65536, round_to=1024,
    )
    plan_scale_4 = resolution_plan(
        "5_2", epsilon=0.0019, scale_over_rc=4.0,
        target_ds_over_epsilon=1.0, min_points=4096, max_points=65536, round_to=1024,
    )
    assert plan_scale_4["selected_points"] > plan_scale_1["selected_points"]
    assert plan_scale_4["selected_points"] <= 65536

    bif = build_bifurcation_atlas(
        ["0_1"], epsilon_values=[0.0019], centerline_points={"0_1": 1024},
        stations=1, angles=3, rho_min=0.0005, rho_max=0.01, bracket_samples=48,
        force_python=True, auto_build=False, reach_pair_points=128,
    )
    assert bif["settings"]["centerline_points_by_knot"] == {"0_1": 1024}
    assert all(0.0 <= row["candidate_surface_fraction"] <= 1.0 for row in bif["rows"])

    project_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "dry_run"
        archive = Path(td) / "dry_run.zip"
        proc = subprocess.run(
            [
                sys.executable, str(project_root / "run_full_campaign.py"),
                "--preset", "smoke", "--skip-build", "--dry-run",
                "--out-root", str(out), "--archive", str(archive),
            ],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        manifest = json.loads((out / "campaign_manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "DRY_RUN"
        assert (out / "campaign_commands.txt").exists()

    print("v0.4.1 tests: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
