"""
Build helper for the local SST internal chi-phase pybind11 extension.

Windows/MSVC note:
    Use a relative C++ source path and a short build-temp directory. If setuptools
    is given an absolute source path on a deep project tree, MSVC can create a very
    long duplicated object path under build/temp/... and fail with:
        fatal error C1083: Cannot open compiler generated file: '': Invalid argument
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Optional

MODULE_NAME = "sst_chi_phase"
CPP_FILENAME = "sst_chi_phase.cpp"
BUILD_TEMP = "_build_tmp"


def package_dir(script_dir: Optional[str] = None) -> str:
    return os.path.abspath(script_dir or os.path.dirname(os.path.abspath(__file__)))


def cpp_path(script_dir: Optional[str] = None) -> str:
    return os.path.join(package_dir(script_dir), CPP_FILENAME)


def _compiled_binaries(base: str):
    old_cwd = os.getcwd()
    try:
        os.chdir(base)
        return [
            f for f in glob.glob(f"{MODULE_NAME}.*")
            if f.endswith(".pyd") or f.endswith(".so")
        ]
    finally:
        os.chdir(old_cwd)


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    base = package_dir(script_dir)
    src = cpp_path(script_dir)
    if not os.path.exists(src):
        return False

    binaries = _compiled_binaries(base)
    if not binaries:
        return True

    latest_binary = max((os.path.join(base, b) for b in binaries), key=os.path.getmtime)
    return os.path.getmtime(src) > os.path.getmtime(latest_binary)


def build_module(script_dir: Optional[str] = None, *, force: bool = False):
    try:
        import pybind11
    except ImportError as exc:
        raise ImportError("pybind11 is not installed. Run `pip install pybind11`.") from exc

    from setuptools import Extension, setup

    base = package_dir(script_dir)
    src = cpp_path(script_dir)
    if not os.path.exists(src):
        raise FileNotFoundError(src)

    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")

    # This kernel does not use OpenMP, so do not pass /openmp. Keeping MSVC flags
    # minimal avoids unrelated compiler/generated-file issues on Python 3.13 setups.
    if os.name == "nt":
        c_args = ["/O2", "/std:c++14"]
        link_args = []
    else:
        c_args = ["-O3", "-std=c++14"]
        link_args = []

    old_cwd = os.getcwd()
    old_argv = list(sys.argv)
    try:
        # Critical: make the source relative to the package dir. This prevents
        # setuptools/MSVC from duplicating the absolute source tree below
        # build/temp... and producing very long object paths.
        os.chdir(base)

        ext_modules = [
            Extension(
                MODULE_NAME,
                [CPP_FILENAME],
                include_dirs=[pybind11.get_include()],
                language="c++",
                extra_compile_args=c_args,
                extra_link_args=link_args,
            )
        ]

        script_args = ["build_ext", "--inplace", "--build-temp", BUILD_TEMP]
        if force:
            script_args.append("--force")

        sys.argv = ["setup.py", *script_args]
        setup(
            name=MODULE_NAME,
            ext_modules=ext_modules,
            script_args=script_args,
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
    """Ensures the module is built. Import it normally after calling this."""
    if needs_recompile(script_dir):
        build_module(script_dir)


if __name__ == "__main__":
    print(f"[*] Manual build trigger for {MODULE_NAME}...")
    force = "--force" in sys.argv
    if force:
        print("[*] Forced rebuild...")
        build_module(force=True)
    elif needs_recompile():
        build_module()
    else:
        print("[*] C++ code is already up-to-date. Use '--force' to rebuild anyway.")
    print(f"[*] {MODULE_NAME} is ready for use.")
