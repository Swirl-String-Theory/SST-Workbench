
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def load(name):
    return json.loads((ROOT / "configs" / name).read_text(encoding="utf-8"))

def test_extended_configs_match_m128_except_intended_fields():
    base = load("qm_full_filtered_m128.json")
    allowed = {"name", "qm_sample_n", "spectral_cutoff_mode", "energy_normalization_reference"}
    for cutoff, n in [(160, 960), (192, 1152)]:
        cfg = load(f"qm_full_filtered_m{cutoff}.json")
        assert cfg["spectral_cutoff_mode"] == cutoff
        assert cfg["qm_sample_n"] == n
        differing = {k for k in set(base) | set(cfg) if base.get(k) != cfg.get(k)}
        assert differing <= allowed

def test_extended_runner_help_and_dry_run(tmp_path):
    help_run = subprocess.run(
        [sys.executable, str(ROOT/"scripts"/"run_qm_spectral_extended.py"), "--help"],
        cwd=ROOT, capture_output=True, text=True, check=True
    )
    assert "-Previous" in help_run.stdout
    out = tmp_path / "dry"
    subprocess.run(
        [sys.executable, str(ROOT/"scripts"/"run_qm_spectral_extended.py"),
         "-NoBaseline", "-Ids", "L6a4", "-Output", str(out), "--dry-run"],
        cwd=ROOT, capture_output=True, text=True, check=True
    )
    plan = json.loads((out/"extended_ladder_plan.json").read_text(encoding="utf-8"))
    assert plan["ids"] == ["L6a4"]
    assert [s["cutoff"] for s in plan["stages"]] == [160, 192]
