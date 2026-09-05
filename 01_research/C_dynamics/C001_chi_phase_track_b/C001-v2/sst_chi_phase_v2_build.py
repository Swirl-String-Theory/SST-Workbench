"""Build helper for the local SST chi-phase v2 pybind11 extension.

Windows/MSVC notes:
- The Extension source is intentionally RELATIVE (CPP_FILENAME), not absolute.
  This avoids MSVC object-path failures such as C1083 with an empty generated file.
- build-temp is kept short (_build_tmp).
- OpenMP is not required for this small verification kernel.
"""

from __future__ import annotations

import glob
import os
import sys
from typing import Optional

MODULE_NAME = "sst_chi_phase_v2"
CPP_FILENAME = "sst_chi_phase_v2.cpp"


def package_dir(script_dir: Optional[str] = None) -> str:
    return script_dir or os.path.dirname(os.path.abspath(__file__))


def cpp_path(script_dir: Optional[str] = None) -> str:
    return os.path.join(package_dir(script_dir), CPP_FILENAME)


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    base = package_dir(script_dir)
    src = cpp_path(script_dir)
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

    base = package_dir(script_dir)
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
            [CPP_FILENAME],  # relative path: important for MSVC
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
    """Ensures the module is built. Import it normally after calling this."""
    if needs_recompile(script_dir):
        build_module(script_dir)


if __name__ == "__main__":
    print(f"[*] Manual build trigger for {MODULE_NAME}...")
    if "--force" in sys.argv:
        print("[*] Forced rebuild...")
        build_module()
    elif needs_recompile():
        build_module()
    else:
        print("[*] C++ code is already up-to-date. Use '--force' to rebuild anyway.")
    print(f"[*] {MODULE_NAME} is ready for use.")
