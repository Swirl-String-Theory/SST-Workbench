"""Windows/Linux/macOS-safe local autobuild helper for the SST torsion-impedance pybind11 backend.

The helper recompiles automatically when ``src/sst_torsion_impedance.cpp`` is newer
than the compiled extension, or when no compiled extension exists. It optionally
supports a compact ``pybind11_headers.zip`` placed next to this file; otherwise it
uses an installed ``pybind11`` package.
"""
from __future__ import annotations

import glob
import importlib
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import List, Optional

MODULE_NAME = "sst_torsion_impedance"
CPP_FILENAME = "sst_torsion_impedance.cpp"
CPP_SUBDIR = "src"
HEADER_ZIP = "pybind11_headers.zip"
HEADER_DIR = "_pybind11_include"
BUILD_TEMP = "_build_tmp"


def base_dir(script_dir: Optional[str] = None) -> str:
    return script_dir or os.path.dirname(os.path.abspath(__file__))


def cpp_path(base: str) -> str:
    return os.path.join(base, CPP_SUBDIR, CPP_FILENAME)


def _compiled_extensions(base: str) -> List[str]:
    return [
        f for f in glob.glob(os.path.join(base, f"{MODULE_NAME}.*"))
        if f.endswith(".pyd") or f.endswith(".so")
    ]


def needs_recompile(script_dir: Optional[str] = None) -> bool:
    """Return True when the extension is missing or older than the C++ source."""
    base = base_dir(script_dir)
    src = cpp_path(base)
    if not os.path.exists(src):
        raise FileNotFoundError(f"C++ source not found: {src}")
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


def _include_dirs(base: str) -> List[str]:
    bundled = _ensure_zipped_pybind11_headers(base)
    if bundled is not None:
        return [bundled]
    try:
        import pybind11  # type: ignore
        return [pybind11.get_include()]
    except ImportError as exc:
        raise ImportError(
            "pybind11 headers not found. Put pybind11_headers.zip in this folder "
            "or run `python -m pip install pybind11`."
        ) from exc


def clean(script_dir: Optional[str] = None) -> None:
    """Remove local build temporaries, without deleting compiled extensions."""
    base = base_dir(script_dir)
    for rel in (BUILD_TEMP, HEADER_DIR):
        target = os.path.join(base, rel)
        if os.path.isdir(target):
            shutil.rmtree(target)


def build_module(script_dir: Optional[str] = None):
    """Build the pybind11 extension in-place and return the imported module."""
    from setuptools import Extension, setup

    base = base_dir(script_dir)
    src_rel = os.path.join(CPP_SUBDIR, CPP_FILENAME)
    include_dirs = _include_dirs(base)
    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")

    if os.name == "nt":
        c_args = ["/O2", "/std:c++17", "/DBUILD_PYBIND11_MODULE"]
    else:
        c_args = ["-O3", "-std=c++17", "-DBUILD_PYBIND11_MODULE"]

    ext_modules = [
        Extension(
            MODULE_NAME,
            [src_rel],
            include_dirs=include_dirs,
            language="c++",
            extra_compile_args=c_args,
        )
    ]

    old_cwd = os.getcwd()
    old_argv = list(sys.argv)
    try:
        os.chdir(base)
        sys.argv = [
            "setup.py",
            "build_ext",
            "--inplace",
            "--build-temp",
            BUILD_TEMP,
        ]
        setup(
            name=MODULE_NAME,
            ext_modules=ext_modules,
            script_args=["build_ext", "--inplace", "--build-temp", BUILD_TEMP],
        )
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv

    importlib.invalidate_caches()
    return importlib.import_module(MODULE_NAME)


def import_module(*, auto_build: bool = True, script_dir: Optional[str] = None):
    """Import the extension, building it first when needed."""
    base = base_dir(script_dir)
    if base not in sys.path:
        sys.path.insert(0, base)
    if auto_build and needs_recompile(script_dir):
        return build_module(script_dir)
    return importlib.import_module(MODULE_NAME)


def main() -> int:
    if "--clean" in sys.argv:
        clean()
        print(f"[*] Removed {BUILD_TEMP}/ and {HEADER_DIR}/ if present.")
        return 0
    if "--force" in sys.argv:
        build_module()
        return 0
    if needs_recompile():
        build_module()
    else:
        print(f"[*] {MODULE_NAME} is already up to date. Use --force to rebuild.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
