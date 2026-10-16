from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_regime_is_reset_plus_collision_fast_without_geometry_overrides():
    s=(ROOT/'tools/run_knotplot_campaign.py').read_text()
    assert "'reset all','collision fast'" in s
    for bad in ('fitto mindist','max-dr =','close =','stusplit =','timeincr ='):
        assert bad not in s
