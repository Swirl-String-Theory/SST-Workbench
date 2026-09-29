from pathlib import Path
import re


def test_native_has_no_unqualified_ssize_t():
    source = (Path(__file__).resolve().parents[1] / "cpp" / "native.cpp").read_text(encoding="utf-8")
    # Bare ssize_t is POSIX-oriented and fails with MSVC. py::ssize_t is portable via pybind11.
    assert re.search(r"(?<![\w:])ssize_t\b", source) is None
    assert "py::ssize_t" in source
