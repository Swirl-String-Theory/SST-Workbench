from pathlib import Path


def test_native_source_uses_pybind_ssize_t_not_posix_ssize_t():
    root = Path(__file__).resolve().parents[1]
    text = (root / "cpp" / "native.cpp").read_text(encoding="utf-8")
    assert "for (ssize_t " not in text
    assert "static_cast<ssize_t>" not in text
    assert " py::ssize_t " in text or "py::ssize_t>" in text


def test_windows_builder_does_not_fallback_to_mingw_direct_link():
    root = Path(__file__).resolve().parents[1]
    text = (root / "src" / "maxwell_sst_falsifier" / "native_ext" / "build_ext_if_needed.py").read_text(encoding="utf-8")
    assert 'if platform.system().lower()=="windows":\n        ok=_build_with_setuptools(out,verbose)' in text


def test_failed_native_build_is_cached_to_prevent_log_spam():
    root = Path(__file__).resolve().parents[1]
    text = (root / "src" / "maxwell_sst_falsifier" / "native_ext" / "build_ext_if_needed.py").read_text(encoding="utf-8")
    assert 'FAIL_STAMP=BUILD/"native.failed.json"' in text
    assert "previous build attempt failed for unchanged source" in text
