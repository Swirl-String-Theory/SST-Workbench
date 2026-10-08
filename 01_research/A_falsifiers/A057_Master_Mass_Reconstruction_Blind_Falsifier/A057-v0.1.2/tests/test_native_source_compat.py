from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pybind11_3_handle_conversion_is_explicit():
    src = (ROOT / "native_ext" / "mm_native.cpp").read_text(encoding="utf-8")
    assert "ArrayF64C::ensure(obj)" in src
    assert "py::array_t<double,py::array::c_style|py::array::forcecast>(obj)" not in src.replace(" ", "")


def test_msvc_uses_pybind_ssize_type():
    src = (ROOT / "native_ext" / "mm_native.cpp").read_text(encoding="utf-8")
    assert "py::ssize_t" in src
    # Prevent reintroducing the POSIX-only bare ssize_t loop index that failed under MSVC.
    assert "for(ssize_t" not in src.replace(" ", "")
