"""Regression: every paper-upgrade gate.py --selftest must PASS."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]

# Expected locations after the 2026-09-07 paper-upgrade bundle apply.
EXPECTED_GATES: list[tuple[str, Path]] = [
    ("D006", WB / "01_research/D_benchmarks/D006_minimal_falsification_harness/D006-v0.4.0/paper_upgrade/gate.py"),
    ("C006", WB / "01_research/C_dynamics/C006_kelvin_floquet_workbench/C006-v0.2.0/paper_upgrade/gate.py"),
    ("A037", WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.0/paper_upgrade/gate.py"),
    ("A034", WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.0/paper_upgrade/gate.py"),
    ("A029", WB / "01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0/paper_upgrade/gate.py"),
    ("A030", WB / "01_research/A_falsifiers/A030_material_phase_eft_holonomy/A030-v0.2.0/paper_upgrade/gate.py"),
    ("A023", WB / "01_research/A_falsifiers/A023_multitopology_rpo_floquet/A023-v0.5.0/paper_upgrade/gate.py"),
    ("A031", WB / "01_research/A_falsifiers/A031_adaptive_period_rpo_floquet/A031-v0.2.0/paper_upgrade/gate.py"),
    ("A035", WB / "01_research/A_falsifiers/A035_intrinsic_modal_swirl_clock/A035-v0.3.0/paper_upgrade/gate.py"),
    ("A008", WB / "01_research/A_falsifiers/A008_chiral_kelvin_core/A008-v0.2.0/paper_upgrade/gate.py"),
    ("A038", WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0/paper_upgrade/gate.py"),
    ("A021", WB / "01_research/A_falsifiers/A021_trefoil_lobe_self_confinement/A021-v0.4.0/paper_upgrade/gate.py"),
    ("A024", WB / "01_research/A_falsifiers/A024_threaded_hole_separatrix/_variants/optional-paper-control/paper_upgrade/gate.py"),
    ("A025", WB / "01_research/A_falsifiers/A025_local_thread_texture_boost/_variants/optional-paper-control/paper_upgrade/gate.py"),
    ("A016", WB / "01_research/A_falsifiers/A016_helmholtz_vortex_transport/_variants/optional-paper-control/paper_upgrade/gate.py"),
    ("A036", WB / "01_research/A_falsifiers/A036_scii_intrinsic_modal_phase_clock/A036-v0.1.1/paper_upgrade/gate.py"),
    ("A039", WB / "01_research/A_falsifiers/A039_sciib_frozen_modal_pair_phase_clock/A039-v0.1.1/paper_upgrade/gate.py"),
    ("A040", WB / "01_research/A_falsifiers/A040_sciii_koopman_dmd_phase_clock/A040-v0.1.0/paper_upgrade/gate.py"),
]


def test_expected_gate_count_is_18():
    assert len(EXPECTED_GATES) == 18


@pytest.mark.parametrize("cid,path", EXPECTED_GATES, ids=[c for c, _ in EXPECTED_GATES])
def test_paper_upgrade_gate_selftest(cid: str, path: Path):
    assert path.is_file(), f"{cid}: missing {path}"
    proc = subprocess.run(
        [sys.executable, str(path), "--selftest"],
        cwd=path.parent.parent,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"{cid} selftest failed (rc={proc.returncode}):\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    # stdout should be JSON with status PASS when printed
    out = (proc.stdout or "").strip()
    if out:
        data = json.loads(out)
        assert data.get("status") == "PASS", f"{cid}: {data}"
