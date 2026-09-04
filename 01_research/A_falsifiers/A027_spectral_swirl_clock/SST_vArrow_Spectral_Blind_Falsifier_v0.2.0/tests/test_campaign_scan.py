from pathlib import Path
import json
import numpy as np
import pandas as pd

from sst_v_arrow_falsifier.campaigns import build_recursive_campaign, parse_vortexlab_log


def test_recursive_scan_detects_spectrum_and_diag(tmp_path: Path):
    root = tmp_path / "campaigns"
    (root / "nested").mkdir(parents=True)
    pd.DataFrame({
        "k_rad_m": np.arange(1, 9, dtype=float),
        "omega_rad_s": np.arange(1, 9, dtype=float) * 2.0,
        "power": np.ones(8),
    }).to_csv(root / "nested" / "spectrum.csv", index=False)
    (root / "legacy").mkdir()
    (root / "legacy" / "vortexlab-session.txt").write_text(
        '1. wall=x tPhys=0.500000 type=diag detail={"t":0.5,"Wr":1.0,"ACN":2.0,"RA":3.0,"topologyGap":0.1}\n'
        '2. wall=x tPhys=1.000000 type=diag detail={"t":1.0,"Wr":1.1,"ACN":2.1,"RA":3.1,"topologyGap":0.1}\n',
        encoding="utf-8",
    )
    df, summary = build_recursive_campaign(root, tmp_path / "generated")
    assert len(df) == 1
    assert df.iloc[0].input_type == "spectrum_csv"
    assert summary["n_speed_eligible"] == 1
    assert summary["n_diagnostic_only"] == 1
    diag_files = list((tmp_path / "generated" / "diagnostics").glob("*.csv"))
    assert len(diag_files) == 1
    assert len(pd.read_csv(diag_files[0])) == 2


def test_demo_excluded_by_default(tmp_path: Path):
    root = tmp_path / "campaigns"
    demo = root / "demo_spectrum"
    demo.mkdir(parents=True)
    pd.DataFrame({
        "sample_id":["d"],"input_type":["spectrum_csv"],"path":["d.csv"]
    }).to_csv(demo / "manifest.csv", index=False)
    pd.DataFrame({"k_rad_m":[1,2,3,4,5,6],"omega_rad_s":[1,2,3,4,5,6]}).to_csv(demo / "d.csv",index=False)
    df, summary = build_recursive_campaign(root, tmp_path / "generated")
    assert len(df) == 0
    df2, summary2 = build_recursive_campaign(root, tmp_path / "generated2", include_demo=True)
    assert len(df2) == 1


def test_parse_vortexlab_log_is_diagnostic_only_input(tmp_path: Path):
    p = tmp_path / "s.txt"
    p.write_text('1. wall=x tPhys=2.5 type=diag detail={"t":2.5,"Wr":-3.4,"Lk":0,"ACN":4.2,"RA":0.05,"scaleProbe":1e-15}\n', encoding='utf-8')
    df = parse_vortexlab_log(p)
    assert list(df.tPhys) == [2.5]
    assert abs(df.iloc[0].Wr + 3.4) < 1e-12
