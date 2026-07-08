"""Windows-safe local build helper for the SST ideal-trefoil Biot-Savart pybind11 backend.

The helper recompiles automatically when `sst_trefoil_biot.cpp` is newer than the
compiled extension, or when no compiled extension exists. It keeps the source
package compact by storing pybind11 headers in `pybind11_headers.zip` and
extracting them on first build.
"""
from __future__ import annotations

import glob
import os
import sys
import zipfile
from typing import Optional, List

MODULE_NAME = "sst_trefoil_biot"
CPP_FILENAME = "sst_trefoil_biot.cpp"
HEADER_ZIP = "pybind11_headers.zip"
HEADER_DIR = "_pybind11_include"


def base_dir(script_dir: Optional[str] = None) -> str:
    return script_dir or os.path.dirname(os.path.abspath(__file__))


def _compiled_extensions(base: str) -> List[str]:
    return [
        f for f in glob.glob(os.path.join(base, f"{MODULE_NAME}.*"))
        if f.endswith(".pyd") or f.endswith(".so")
    ]


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    """Return True if the C++ extension is missing or older than the .cpp source."""
    base = base_dir(script_dir)
    src = os.path.join(base, CPP_FILENAME)
    if not os.path.exists(src):
        return False
    binaries = _compiled_extensions(base)
    if not binaries:
        return True
    latest_binary_mtime = max(os.path.getmtime(f) for f in binaries)
    return os.path.getmtime(src) > latest_binary_mtime


def _ensure_zipped_pybind11_headers(base: str) -> Optional[str]:
    include_dir = os.path.join(base, HEADER_DIR)
    header = os.path.join(include_dir, "pybind11", "pybind11.h")
    if os.path.exists(header):
        return include_dir

    zip_path = os.path.join(base, HEADER_ZIP)
    if not os.path.exists(zip_path):
        return None

    print(f"[*] Extracting bundled pybind11 headers from {HEADER_ZIP}...")
    os.makedirs(include_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(include_dir)

    if not os.path.exists(header):
        raise RuntimeError(f"{HEADER_ZIP} did not contain pybind11/pybind11.h")
    return include_dir


def _include_dirs(base: str):
    bundled = _ensure_zipped_pybind11_headers(base)
    if bundled is not None:
        return [bundled]
    try:
        import pybind11
        return [pybind11.get_include()]
    except ImportError as exc:
        raise ImportError(
            "pybind11 headers not found. Keep pybind11_headers.zip in this folder "
            "or run `pip install pybind11`."
        ) from exc


def build_module(script_dir: Optional[str] = None):
    from setuptools import Extension, setup

    base = base_dir(script_dir)
    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")
    c_args = ["/O2", "/std:c++14"] if os.name == "nt" else ["-O3", "-std=c++14"]
    ext_modules = [
        Extension(
            MODULE_NAME,
            [CPP_FILENAME],
            include_dirs=_include_dirs(base),
            language="c++",
            extra_compile_args=c_args,
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


if __name__ == "__main__":
    if "--force" in sys.argv:
        build_module()
    elif needs_recompile():
        build_module()
    else:
        print(f"[*] {MODULE_NAME} is already up to date. Use --force to rebuild.")
