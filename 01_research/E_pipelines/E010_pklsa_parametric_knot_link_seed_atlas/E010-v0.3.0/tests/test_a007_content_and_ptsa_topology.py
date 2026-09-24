from pathlib import Path

from pklsa_builder.repo_finder import _classify_catalog_file
from pklsa_builder.source_discovery import _representation_from_record, topology_from_path


def test_a007_three_column_fseries_is_xyz(tmp_path: Path):
    root = tmp_path / 'Sources' / 'FourierSeries_Fremlin'
    root.mkdir(parents=True)
    p = root / 'knot.4_1p.fseries'
    p.write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n', encoding='utf-8')
    role, hint = _classify_catalog_file(p, 'A007', tmp_path)
    assert role == 'source_geometry'
    assert hint == 'xyz_text'
    rec = {'path': str(p), 'representation_hint': hint}
    assert _representation_from_record(rec, 'fremlin_fourier_mirror') == 'xyz'


def test_a007_six_column_fseries_remains_fourier(tmp_path: Path):
    root = tmp_path / 'Sources' / 'FourierSeries_Fremlin'
    root.mkdir(parents=True)
    p = root / 'knot.4_1.fseries'
    p.write_text('1 2 3 4 5 6\n2 3 4 5 6 7\n3 4 5 6 7 8\n', encoding='utf-8')
    role, hint = _classify_catalog_file(p, 'A007', tmp_path)
    assert role == 'source_geometry'
    assert hint == 'fseries'
    rec = {'path': str(p), 'representation_hint': hint}
    assert _representation_from_record(rec, 'fremlin_fourier_mirror') == 'fremlin_fseries'


def test_hash_fragment_is_not_ht_topology():
    assert topology_from_path(r'C:\\x\\candidates\\PTSA_48a4f951ee3c.xyz') is None
    assert topology_from_path(r'C:\\x\\11a_247\\curve.xyz') == '11a_247'
    assert topology_from_path(r'C:\\x\\L10a174\\curve.xyz') == 'L10a174'
