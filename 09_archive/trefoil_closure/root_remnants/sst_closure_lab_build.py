"""
Build helper for the local trefoil-closure pybind11 extension.

This module is intentionally named ``sst_closure_lab`` (not ``sst_core``) so it
does not collide with the pip/CMake package ``sstcore`` / ``SSTcore``.
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Optional

MODULE_NAME = "sst_closure_lab"
CPP_FILENAME = "sst_closure_lab.cpp"
# Legacy filenames kept for recompile detection cleanup only.
LEGACY_MODULE_NAMES = ("sst_core",)


def cpp_path(script_dir: Optional[str] = None) -> str:
    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, CPP_FILENAME)


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    src = cpp_path(script_dir)
    if not os.path.exists(src):
        return False

    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)

    binaries = [
        f
        for f in glob.glob(f"{MODULE_NAME}.*")
        if f.endswith(".pyd") or f.endswith(".so")
    ]
    if not binaries:
        return True

    latest_binary = max(binaries, key=os.path.getmtime)
    return os.path.getmtime(src) > os.path.getmtime(latest_binary)


def build_module(script_dir: Optional[str] = None, verbose: bool = True) -> None:
    import pybind11
    from setuptools import Extension, setup

    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    src = cpp_path(base)

    if verbose:
        print(f"[*] Bouwen van {MODULE_NAME} ({CPP_FILENAME}) via pybind11...")

    if sys.platform == "win32":
        c_args = ["/O2", "/std:c++14", "/openmp"]
        link_args: list[str] = []
    else:
        c_args = ["-O3", "-std=c++14", "-fopenmp"]
        link_args = ["-fopenmp"]

    ext_modules = [
        Extension(
            MODULE_NAME,
            [src],
            include_dirs=[pybind11.get_include()],
            language="c++",
            extra_compile_args=c_args,
            extra_link_args=link_args,
        ),
    ]

    old_cwd = os.getcwd()
    old_argv = list(sys.argv)
    try:
        os.chdir(base)
        sys.argv = ["setup.py", "build_ext", "--inplace"]
        setup(
            name=MODULE_NAME,
            ext_modules=ext_modules,
            script_args=["build_ext", "--inplace"],
        )
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv


def import_module(*, auto_build: bool = True, script_dir: Optional[str] = None):
    if auto_build and needs_recompile(script_dir):
        build_module(script_dir)

    import importlib

    mod = importlib.import_module(MODULE_NAME)
    return mod


def ensure_module(script_dir: Optional[str] = None, required_attr: Optional[str] = None):
    """Import ``sst_closure_lab``, rebuilding if source is newer than the binary."""
    import importlib

    if needs_recompile(script_dir):
        build_module(script_dir)

    mod = importlib.import_module(MODULE_NAME)
    if required_attr and not hasattr(mod, required_attr):
        build_module(script_dir)
        mod = importlib.reload(importlib.import_module(MODULE_NAME))
    return mod
