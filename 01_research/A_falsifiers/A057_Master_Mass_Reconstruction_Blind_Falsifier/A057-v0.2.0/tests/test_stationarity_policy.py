from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_stationarity_threshold_tightens_with_authority():
    b=json.loads((ROOT/"configs/basic.json").read_text())
    f=json.loads((ROOT/"configs/full.json").read_text())
    c=json.loads((ROOT/"configs/certify.json").read_text())
    assert b["stationarity_gradient_over_energy_max"] > f["stationarity_gradient_over_energy_max"] > c["stationarity_gradient_over_energy_max"]
    assert c["stationarity_gradient_over_energy_max"] == 0.01
