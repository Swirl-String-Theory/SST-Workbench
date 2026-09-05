from pathlib import Path
import json

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.continuum import audit_link_continuum
from sst_link_suite.native_ext import BackendOptions

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "idealLinks.txt"


def test_continuum_audit_smoke_python_backend():
    cfg = json.loads((ROOT / "configs" / "qm_quick.json").read_text())
    cfg["continuum_sample_ns"] = [32, 64]
    cfg["continuum_relative_tolerance"] = 1.0
    result = audit_link_continuum(
        parse_ideal_links(DATA)["L2a1"], cfg, BackendOptions(force_python=True)
    )
    assert result["sample_ns"] == [32, 64]
    assert result["self_exclusion_energy_arc_D"] == cfg["self_exclusion_energy_arc_D"]
    assert result["sector_convergence"]
