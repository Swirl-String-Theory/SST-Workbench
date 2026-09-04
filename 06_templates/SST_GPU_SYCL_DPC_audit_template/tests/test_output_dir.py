"""Tests for package_root / default_output_dir helpers."""

from __future__ import annotations

from native_ext import _config


def test_package_root_is_template_folder() -> None:
    root = _config.package_root()
    assert root.is_dir()
    assert (root / "native_ext" / "_config.py").is_file()
    assert (root / "run_all_checks.py").is_file()


def test_default_output_dir_matches_folder_name() -> None:
    root = _config.package_root()
    out = _config.default_output_dir()
    assert out.parent == root
    assert out.name == f"{root.name}_outputs"
