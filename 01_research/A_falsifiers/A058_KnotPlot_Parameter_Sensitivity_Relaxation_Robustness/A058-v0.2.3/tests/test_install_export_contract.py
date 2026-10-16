from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_install_contract_exactly_one_export_and_no_long_fixed_relax():
    s=(ROOT/'tools/install_test_export.py').read_text()
    assert "exports!=[geom]" in s
    assert "'go 1'" in s
    assert 'ago 1000' not in s.lower() and 'ago 15000' not in s.lower()
def test_install_uses_sector_context_defaults():
    s=(ROOT/'tools/install_test_export.py').read_text()
    assert "sector_defaults" in s
    assert "f'{sw} = on'" in s
    assert 'slider parameter not reported after enabling' in s
