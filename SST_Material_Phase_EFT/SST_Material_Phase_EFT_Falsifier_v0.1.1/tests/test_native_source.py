from pathlib import Path


def test_native_source_is_msvc_portable():
    src=(Path(__file__).resolve().parents[1]/'native_ext'/'_native.cpp').read_text(encoding='utf-8')
    assert 'Py_ssize_t' in src
    scrub=src.replace('Py_ssize_t','')
    assert 'ssize_t' not in scrub
    assert '#ifdef _OPENMP' in src
