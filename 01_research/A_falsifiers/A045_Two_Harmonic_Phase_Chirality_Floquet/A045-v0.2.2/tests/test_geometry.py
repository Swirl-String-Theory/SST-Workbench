from pathlib import Path
from sst_thpcf.geometry import load_curve, prepare_curve, segment_stats

def test_frozen_seed_loads():
    p=Path(__file__).parents[1]/"data/frozen/a038/R6B8AC59A7F65A9.npy"
    X=prepare_curve(load_curve(p),48)
    assert X.shape==(48,3)
    _,cv=segment_stats(X)
    assert cv < 0.05
