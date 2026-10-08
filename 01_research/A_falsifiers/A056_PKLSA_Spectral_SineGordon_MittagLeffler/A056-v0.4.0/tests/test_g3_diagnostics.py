from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]


def _load_tool():
    p = ROOT / "tools" / "diagnose_g3.py"
    spec = importlib.util.spec_from_file_location("a056_diag_g3", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_g3_diagnostic_uses_frozen_science_functions_and_is_read_only():
    mod = _load_tool()
    cfg = json.loads((ROOT / "configs" / "e010_real_score.json").read_text(encoding="utf-8"))
    from a056_science.io import discover_cases
    cases = discover_cases(ROOT / "data" / "synthetic_blind")
    assert cases
    before = sorted((p.name, p.stat().st_size) for p in (ROOT / "data" / "synthetic_blind").iterdir())
    row = mod.diagnose_case(cases[0], cfg)
    after = sorted((p.name, p.stat().st_size) for p in (ROOT / "data" / "synthetic_blind").iterdir())
    assert before == after
    assert row["opaque_id"]
    assert row["phase"]["best_discovery_model"] in {"W", "KG", "DUFFING", "SG"}
    assert set(row["phase"]["models"]) == {"W", "KG", "DUFFING", "SG"}
    assert row["memory"] is not None
    assert set(row["memory"]["models"]) == {"EXP", "STRETCHED", "BIEXP", "ML"}
    assert row["posthoc_warning"].startswith("Holdout metrics are diagnostic only")


def test_g3_diagnostic_does_not_touch_frozen_protocol_files():
    frozen = json.loads((ROOT / "preregistration" / "FROZEN_PROTOCOL.json").read_text(encoding="utf-8"))
    frozen_paths = {x["path"] for x in frozen["files"]}
    assert "tools/diagnose_g3.py" not in frozen_paths
    assert "run_diagnose_g3.cmd" not in frozen_paths
