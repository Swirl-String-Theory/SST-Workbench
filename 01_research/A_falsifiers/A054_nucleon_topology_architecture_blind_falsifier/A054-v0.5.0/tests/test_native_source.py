from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_pybind11_3_compatible_source():
 s=(ROOT/'native_ext'/'a054_native.cpp').read_text();assert 'py::ssize_t' in s;assert 'ArrayF64C::ensure' in s;assert 'PYBIND11_MODULE(a054_native' in s
