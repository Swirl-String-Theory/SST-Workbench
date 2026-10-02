from pathlib import Path
from sklsa.selection import load_selection, selected_ids

HERE = Path(__file__).resolve().parents[1]


def test_selection_scope():
    cfg = load_selection(HERE / "configs" / "selected_topologies.json")
    assert len(cfg["core_knots"]) == 35
    selected = selected_ids(cfg)
    assert len(selected) == 45
    assert "8_5" in selected
    assert "L6a4" in selected
    assert "9_1" not in selected


def test_sentinels_are_opt_in():
    cfg = load_selection(HERE / "configs" / "selected_topologies.json")
    selected = selected_ids(cfg, include_sentinels=True)
    assert "9_1" in selected and "11_2" in selected
