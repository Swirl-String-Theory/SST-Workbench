from pathlib import Path
import json

from sst_link_suite.parser import parse_ideal_links
from sst_link_suite.qm_readiness import analyze_qm_readiness
from sst_link_suite.native_ext import BackendOptions, backend_status

ROOT = Path(__file__).parents[1]
DATA = ROOT / "data" / "idealLinks.txt"


def test_qm_readiness_smoke_hopf():
    cfg = json.loads((ROOT / "configs" / "qm_quick.json").read_text())
    cfg["qm_sample_n"] = 24
    cfg["mode_max"] = 0
    cfg["max_independent_sectors"] = 1
    cfg["plots"] = False
    options = BackendOptions(force_python=True)
    result = analyze_qm_readiness(
        parse_ideal_links(DATA)["L2a1"], cfg, options, backend_status(options)
    )
    from sst_link_suite import __version__
    assert result["suite_version"] == __version__
    assert result["sector_results"]
    assert "candidate_symplectic_form" in result["sector_results"][0]
    assert "readiness" in result["sector_results"][0]
