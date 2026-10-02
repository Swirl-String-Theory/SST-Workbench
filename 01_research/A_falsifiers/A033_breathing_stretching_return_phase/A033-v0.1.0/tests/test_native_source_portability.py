from pathlib import Path
import re


def test_native_cpp_has_no_unqualified_ssize_t():
    src = (Path(__file__).resolve().parents[1] / "cpp" / "native.cpp").read_text(encoding="utf-8")
    stripped = src.replace("py::ssize_t", "")
    assert re.search(r"(?<![A-Za-z0-9_:])ssize_t(?![A-Za-z0-9_])", stripped) is None
