#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py
========
Compile sst_bs_kernel.cpp → sst_bs_kernel.<ext>.so  in the same directory.

Usage
-----
  python3 build.py               # standard build
  python3 build.py --no-omp     # force single-threaded (no OpenMP)
  python3 build.py --clean      # remove .so and rebuild
  python3 build.py --check      # only check whether .so is importable

The script can also be imported and called programmatically:
  import build; build.build()   # returns Path to .so
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC  = HERE / "sst_bs_kernel.cpp"
MOD  = "sst_bs_kernel"


def _ext_suffix() -> str:
    return subprocess.check_output(
        [sys.executable, "-c",
         "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))"],
        text=True,
    ).strip()


def _pybind11_includes() -> list[str]:
    out = subprocess.check_output(
        [sys.executable, "-m", "pybind11", "--includes"],
        text=True,
    ).strip()
    return out.split()


def _so_path() -> Path:
    return HERE / (MOD + _ext_suffix())


def _is_fresh(so: Path) -> bool:
    """True when .so exists and is newer than the .cpp source."""
    return so.exists() and so.stat().st_mtime >= SRC.stat().st_mtime


def build(force: bool = False, omp: bool = True, verbose: bool = True) -> Path:
    """
    Compile sst_bs_kernel.cpp.

    Parameters
    ----------
    force   : re-compile even if .so is already fresh
    omp     : attempt to enable OpenMP (-fopenmp)
    verbose : print build command

    Returns
    -------
    Path to the compiled .so file.
    """
    so = _so_path()

    if not force and _is_fresh(so):
        if verbose:
            print(f"[build] {so.name} is up to date.")
        return so

    try:
        includes = _pybind11_includes()
    except Exception as e:
        print(f"[build] ERROR: could not get pybind11 includes: {e}")
        print("        Run:  pip install pybind11 --break-system-packages")
        sys.exit(1)

    ext = _ext_suffix()

    cmd_base = [
        "g++",
        "-O3", "-march=native",
        "-shared", "-std=c++17", "-fPIC",
        *includes,
        str(SRC),
        "-o", str(so),
    ]

    # -- try with OpenMP first, fall back without --
    tried = []
    for use_omp in ([True, False] if omp else [False]):
        cmd = cmd_base[:]
        if use_omp:
            cmd.insert(1, "-fopenmp")
        tried.append(cmd)
        if verbose:
            print(f"[build] {'(OpenMP) ' if use_omp else '(single) '}$ " +
                  " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if verbose:
                print(f"[build] OK → {so.name}")
            return so
        if verbose:
            print(f"[build] stderr: {result.stderr.strip()}")

    print("[build] FATAL: compilation failed. Commands tried:")
    for c in tried:
        print("  " + " ".join(c))
    sys.exit(1)


def check() -> bool:
    """Try to import the compiled module; return True on success."""
    so = _so_path()
    if not so.exists():
        print(f"[build] {so.name} not found — run  python3 build.py  first.")
        return False
    sys.path.insert(0, str(HERE))
    try:
        mod = importlib.import_module(MOD)
        omp_str = f"OpenMP ON ({mod.n_threads} threads)" if mod.openmp else "OpenMP OFF"
        print(f"[build] import {MOD} OK   [{omp_str}]")
        return True
    except ImportError as e:
        print(f"[build] import {MOD} FAILED: {e}")
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build sst_bs_kernel pybind11 module")
    ap.add_argument("--no-omp",  action="store_true", help="disable OpenMP")
    ap.add_argument("--clean",   action="store_true", help="force rebuild")
    ap.add_argument("--check",   action="store_true", help="only test import")
    args = ap.parse_args()

    if args.check:
        ok = check()
        sys.exit(0 if ok else 1)

    build(force=args.clean, omp=not args.no_omp)
    check()
