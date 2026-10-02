from pathlib import Path
import importlib.util


def _load_repo_finder():
    p=Path(__file__).resolve().parents[1]/'pklsa_builder'/'repo_finder.py'
    spec=importlib.util.spec_from_file_location('repo_finder_under_test',p)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a007_header_only_fseries_is_metadata(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'8_5'/'knot.8_5.fseries'
    p.parent.mkdir(parents=True)
    p.write_text('% Knot 8_5\n% coefficient header only\n',encoding='utf-8')
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert (role,rep)==('source_metadata','fseries_header_only_incomplete_mirror')


def test_a007_six_column_fseries_stays_geometry(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'4_1'/'knot.4_1.fseries'
    p.parent.mkdir(parents=True)
    p.write_text('% Fourier\n1 2 3 4 5 6\n7 8 9 10 11 12\n',encoding='utf-8')
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert role=='source_geometry'
    assert rep=='fseries'


def test_a007_optional_a0_fseries_stays_geometry(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'4_1'/'knot.4_1d.fseries'
    p.parent.mkdir(parents=True)
    p.write_text('% Fourier\n0.1 0.2 0.3\n1 2 3 4 5 6\n7 8 9 10 11 12\n',encoding='utf-8')
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert role=='source_geometry'
    assert rep=='fseries'


def test_a007_xyz_disguised_fseries_stays_xyz_geometry(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'4_1'/'knot.4_1x.fseries'
    p.parent.mkdir(parents=True)
    p.write_text('0 0 0\n1 0 0\n1 1 0\n0 1 0\n',encoding='utf-8')
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert (role,rep)==('source_geometry','xyz_text')


def test_noncomment_malformed_fseries_is_not_silently_demoted(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'4_1'/'bad.fseries'
    p.parent.mkdir(parents=True)
    p.write_text('% Fourier\nthis is malformed data\n',encoding='utf-8')
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert role=='source_geometry'
    assert rep=='fseries'


def test_realistic_8_5_header_only_is_marked_incomplete_mirror(tmp_path):
    m=_load_repo_finder()
    root=tmp_path/'A007_knot_library'
    p=root/'Sources'/'FourierSeries_Fremlin'/'original'/'8_5'/'knot.8_5.fseries'
    p.parent.mkdir(parents=True)
    p.write_text(
        '% Knot 8_5 (DHF, based on Knotinfo diagram)\n'
        '% process with doknotscad\n'
        '% calculated with knotadjust.f\n'
        '% lines  a_x(j) b_x(j)  a_y(j)  b_y(j)  a_z(j)  b_z(j)\n',
        encoding='utf-8'
    )
    role,rep=m._classify_catalog_file(p,'A007',root)
    assert role=='source_metadata'
    assert rep=='fseries_header_only_incomplete_mirror'
