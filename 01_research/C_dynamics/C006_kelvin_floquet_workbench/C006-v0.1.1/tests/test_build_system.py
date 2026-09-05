from __future__ import annotations

import sys
from pathlib import Path

from sst_kelvin_workbench import build_ext_if_needed as b


def test_windows_link_args_select_single_existing_import_library(monkeypatch, tmp_path: Path):
    maj, minor = sys.version_info[:2]
    (tmp_path / f"python{maj}{minor}.lib").write_bytes(b"")
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.setattr(b, "_candidate_python_lib_dirs", lambda: [tmp_path])
    args = b._python_link_args_for_windows()
    link_args = [x for x in args if x.startswith("-l")]
    assert link_args == [f"-lpython{maj}{minor}"]
    assert f"-lpython{maj}.{minor}" not in args


def test_windows_link_args_fallback_is_single_name(monkeypatch):
    maj, minor = sys.version_info[:2]
    monkeypatch.setattr(b.platform, "system", lambda: "Windows")
    monkeypatch.setattr(b, "_candidate_python_lib_dirs", lambda: [])
    args = b._python_link_args_for_windows()
    assert args == [f"-lpython{maj}{minor}"]


def test_setuptools_fallback_declares_only_real_python_package():
    src = b._setuptools_setup_source()
    assert "packages=['sst_kelvin_workbench']" in src
    assert "Extension('sst_kelvin_workbench._native'" in src
