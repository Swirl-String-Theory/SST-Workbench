from pathlib import Path
from maxwell_sst_falsifier.campaign import run_campaign

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_pass_is_demo_only_and_has_no_physical_failures():
    r = run_campaign(ROOT / "examples" / "synthetic_pass" / "config.json")
    assert r["overall_verdict"] == "DEMO_ONLY"
    assert not r["physical_failures"]


def test_synthetic_fail_triggers_internal_failures_but_stays_demo_only():
    r = run_campaign(ROOT / "examples" / "synthetic_fail" / "config.json")
    assert r["overall_verdict"] == "DEMO_ONLY"
    assert any(x["gate"] == "GAP" for x in r["physical_failures"])
    assert any(x["gate"] == "SPECTROSCOPIC" for x in r["physical_failures"])
