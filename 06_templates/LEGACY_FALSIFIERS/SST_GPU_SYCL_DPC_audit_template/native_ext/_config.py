"""Project knobs — edit these when you copy the template."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Python package folder name (this directory).
PACKAGE_NAME = "native_ext"

# pybind11 module basename -> native_ext/_native*.pyd / .so
EXT_BASENAME = "_native"

# C++ source relative to project root (parent of PACKAGE_NAME).
CPP_REL = Path("cpp") / "native.cpp"

# Standalone SYCL device probe (not part of the pybind module).
PROBE_CPP_REL = Path("cpp") / "list_sycl_devices.cpp"

# Stamp file under build/ (hash-based rebuild).
STAMP_BASENAME = "native.stamp.json"

# Log prefix for build messages.
LOG_PREFIX = "[sst_gpu]"

# Session-scoped oneAPI bin candidates (no permanent Windows PATH required).
_ONEAPI_ROOTS = (
    Path(r"C:\Program Files (x86)\Intel\oneAPI"),
    Path(r"C:\Program Files\Intel\oneAPI"),
)
_ONEAPI_REL_BINS = (
    Path("compiler") / "latest" / "bin",
    Path("tbb") / "latest" / "bin",
    Path("mkl") / "latest" / "bin",
)

_dll_dirs_registered: set[str] = set()


def package_root() -> Path:
    """Project root (parent of the native_ext package folder)."""
    return Path(__file__).resolve().parent.parent


def default_output_dir() -> Path:
    """Inside-package outputs: ``{folder_name}_outputs``."""
    root = package_root()
    return root / f"{root.name}_outputs"


def oneapi_bin_dirs() -> list[Path]:
    """Existing oneAPI runtime bin directories (compiler / TBB / MKL)."""
    found: list[Path] = []
    seen: set[str] = set()
    for root in _ONEAPI_ROOTS:
        for rel in _ONEAPI_REL_BINS:
            cand = root / rel
            key = str(cand).lower()
            if cand.is_dir() and key not in seen:
                seen.add(key)
                found.append(cand)
    return found


def ensure_oneapi_dll_directories() -> list[str]:
    """Register oneAPI bins via ``os.add_dll_directory`` (Windows only, idempotent)."""
    if sys.platform != "win32":
        return []
    add_dll = getattr(os, "add_dll_directory", None)
    if add_dll is None:
        return []
    registered: list[str] = []
    for directory in oneapi_bin_dirs():
        key = str(directory.resolve())
        if key in _dll_dirs_registered:
            registered.append(key)
            continue
        try:
            add_dll(key)
            _dll_dirs_registered.add(key)
            registered.append(key)
        except OSError:
            continue
    return registered
