"""Build helper for local SST chi-phase v3 pybind11 extension.

Windows-safe: compile from the package directory using a relative source path and a
short build-temp directory, avoiding MSVC object-path failures.
"""
from __future__ import annotations

import glob
import os
import sys
from typing import Optional

MODULE_NAME = "sst_chi_phase_v3"
CPP_FILENAME = "sst_chi_phase_v3.cpp"


def package_dir(script_dir: Optional[str] = None) -> str:
    return script_dir or os.path.dirname(os.path.abspath(__file__))


def cpp_path(script_dir: Optional[str] = None) -> str:
    return os.path.join(package_dir(script_dir), CPP_FILENAME)


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    base = package_dir(script_dir)
    src = cpp_path(base)
    if not os.path.exists(src):
        return False

    old = os.getcwd()
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
        os.chdir(old)


def build_module(script_dir: Optional[str] = None, force: bool = False):
    try:
        import pybind11
    except ImportError as exc:
        raise ImportError("pybind11 is not installed. Run `pip install pybind11`.") from exc

    from setuptools import Extension, setup

    base = package_dir(script_dir)
    if not os.path.exists(cpp_path(base)):
        raise FileNotFoundError(cpp_path(base))

    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")

    if os.name == "nt":
        c_args = ["/O2", "/std:c++14"]
        link_args: list[str] = []
    else:
        c_args = ["-O3", "-std=c++14"]
        link_args = []

    ext_modules = [
        Extension(
            MODULE_NAME,
            [CPP_FILENAME],  # relative source path: important for MSVC
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
        script_args = ["build_ext", "--inplace", "--build-temp", "_build_tmp"]
        if force:
            script_args.append("--force")
        sys.argv = ["setup.py"] + script_args
        setup(name=MODULE_NAME, ext_modules=ext_modules, script_args=script_args)
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv


def import_module(*, auto_build: bool = True, script_dir: Optional[str] = None):
    base = package_dir(script_dir)
    if auto_build and needs_recompile(base):
        build_module(base)
    import importlib
    old = os.getcwd()
    try:
        os.chdir(base)
        return importlib.import_module(MODULE_NAME)
    finally:
        os.chdir(old)


def ensure_module(script_dir: Optional[str] = None):
    base = package_dir(script_dir)
    if needs_recompile(base):
        build_module(base)


if __name__ == "__main__":
    base = package_dir()
    force = "--force" in sys.argv
    if force or needs_recompile(base):
        build_module(base, force=force)
    else:
        print(f"[*] {MODULE_NAME} is already up to date. Use --force to rebuild.")
    print(f"[*] {MODULE_NAME} is ready.")
