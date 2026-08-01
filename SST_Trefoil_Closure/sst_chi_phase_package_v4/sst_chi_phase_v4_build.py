"""Build helper for the local SST chi-phase v4 pybind11 extension.

Windows-safe: builds from the package directory using a relative source path and
short build-temp, avoiding long MSVC /Fo object paths.
"""
from __future__ import annotations

import glob
import os
import sys
from typing import Optional

MODULE_NAME = "sst_chi_phase_v4"
CPP_FILENAME = "sst_chi_phase_v4.cpp"


def cpp_path(script_dir: Optional[str] = None) -> str:
    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, CPP_FILENAME)


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    src = cpp_path(base)
    if not os.path.exists(src):
        return False

    old_cwd = os.getcwd()
    try:
        os.chdir(base)
        binaries = [
            f for f in glob.glob(f"{MODULE_NAME}.*")
            if f.endswith(".pyd") or f.endswith(".so")
        ]
        if not binaries:
            return True
        latest_binary = max(binaries, key=os.path.getmtime)
        return os.path.getmtime(src) > os.path.getmtime(latest_binary)
    finally:
        os.chdir(old_cwd)


def build_module(script_dir: Optional[str] = None):
    try:
        import pybind11
    except ImportError as exc:
        raise ImportError("pybind11 is not installed. Run `pip install pybind11`.") from exc

    from setuptools import Extension, setup

    base = script_dir or os.path.dirname(os.path.abspath(__file__))
    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")

    if os.name == "nt":
        c_args = ["/O2", "/std:c++14"]
        link_args = []
    else:
        c_args = ["-O3", "-std=c++14"]
        link_args = []

    ext_modules = [
        Extension(
            MODULE_NAME,
            [CPP_FILENAME],  # relative path; avoids MSVC object path bug
            include_dirs=[pybind11.get_include()],
            language="c++",
            extra_compile_args=c_args,
            extra_link_args=link_args,
        )
    ]

    old_cwd = os.getcwd()
    old_argv = list(sys.argv)
    try:
        os.chdir(base)
        sys.argv = ["setup.py", "build_ext", "--inplace", "--build-temp", "_build_tmp"]
        setup(
            name=MODULE_NAME,
            ext_modules=ext_modules,
            script_args=["build_ext", "--inplace", "--build-temp", "_build_tmp"],
        )
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv


def import_module(*, auto_build: bool = True, script_dir: Optional[str] = None):
    if auto_build and needs_recompile(script_dir):
        build_module(script_dir)
    import importlib
    return importlib.import_module(MODULE_NAME)


def ensure_module(script_dir: Optional[str] = None):
    if needs_recompile(script_dir):
        build_module(script_dir)


if __name__ == "__main__":
    if "--force" in sys.argv:
        build_module()
    elif needs_recompile():
        build_module()
    else:
        print(f"[*] {MODULE_NAME} is up to date. Use --force to rebuild.")
