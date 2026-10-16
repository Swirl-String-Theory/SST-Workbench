from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_install_test_is_exactly_one_export_and_no_relaxation():
    t=(ROOT/'tools/install_test_export.py').read_text(encoding='utf-8')
    assert "exports!=[geom]" in t
    assert "'load 3.1'" in t
    assert "'refine nbeads 300'" in t
    assert 'save {geom.resolve().as_posix()} ascii' in t
    assert "'ago " not in t and "'go " not in t
