"""Tests for oneAPI bin discovery and DLL directory registration."""

from __future__ import annotations

from pathlib import Path

from native_ext import _config


def test_oneapi_bin_dirs_only_existing() -> None:
    dirs = _config.oneapi_bin_dirs()
    assert isinstance(dirs, list)
    for d in dirs:
        assert isinstance(d, Path)
        assert d.is_dir()


def test_ensure_oneapi_dll_directories_idempotent() -> None:
    first = _config.ensure_oneapi_dll_directories()
    second = _config.ensure_oneapi_dll_directories()
    assert isinstance(first, list)
    assert isinstance(second, list)
    assert first == second
    for path in first:
        assert Path(path).is_dir()
