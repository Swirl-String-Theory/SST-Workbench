from pathlib import Path
import json
import numpy as np
import pandas as pd

from sst_v_arrow_falsifier.blind import run_blind


def test_recursive_blind_can_return_insufficient_data_for_diag_only(tmp_path: Path):
    root = tmp_path / "campaigns"
    root.mkdir()
    pd.DataFrame({
        "tPhys": np.arange(17),
        "Wr": np.linspace(0,1,17),
        "Lk": np.zeros(17),
        "ACN": np.linspace(4,5,17),
        "RA": np.linspace(.05,.051,17),
    }).to_csv(root / "diag.csv", index=False)
    cfg = Path(__file__).parents[1] / "config" / "default.json"
    out = tmp_path / "out"
    report = run_blind(root, out, cfg, recursive=True)
    assert report["blind_verdict"] == "INSUFFICIENT_DATA"
    assert report["discovery"]["n_diagnostic_only"] == 1
    assert report["pooled_speed"] is None
