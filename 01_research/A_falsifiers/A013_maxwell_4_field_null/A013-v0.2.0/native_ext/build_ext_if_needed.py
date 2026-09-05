from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import json
import subprocess
import sys
import sysconfig
from pathlib import Path

from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[1]
PKG = Path(__file__).resolve().parent
CPP = ROOT / CPP_REL
BUILD = ROOT / "build"
STAMP = BUILD / STAMP_BASENAME


def extension_path() -> Path:
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG / (EXT_BASENAME + suffix)


def _hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _run(cmd: list[str], verbose: bool = True) -> bool:
    if verbose:
        print(LOG_PREFIX, "compile:", " ".join(map(str, cmd)), file=sys.stderr)
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode == 0:
        return True
    if verbose:
        print(LOG_PREFIX, f"build failed: {proc.returncode}", file=sys.stderr)
        print("\n".join((proc.stdout + "\n" + proc.stderr).splitlines()[-80:]), file=sys.stderr)
    return False


def _setup_source(openmp: bool) -> str:
    if openmp:
        return r'''from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11

class BuildExt(build_ext):
    def build_extensions(self):
        for ext in self.extensions:
            if self.compiler.compiler_type == "msvc":
                ext.extra_compile_args = ["/O2", "/std:c++17", "/openmp"]
            else:
                ext.extra_compile_args = ["-O3", "-std=c++17", "-fopenmp"]
                ext.extra_link_args = ["-fopenmp"]
        super().build_extensions()

setup(
    name="sst_maxwell_native",
    ext_modules=[Extension("native_ext._native", ["cpp/native.cpp"], include_dirs=[pybind11.get_include()])],
    cmdclass={"build_ext": BuildExt},
)
'''
    return r'''from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11

class BuildExt(build_ext):
    def build_extensions(self):
        for ext in self.extensions:
            if self.compiler.compiler_type == "msvc":
                ext.extra_compile_args = ["/O2", "/std:c++17"]
            else:
                ext.extra_compile_args = ["-O3", "-std=c++17"]
        super().build_extensions()

setup(
    name="sst_maxwell_native",
    ext_modules=[Extension("native_ext._native", ["cpp/native.cpp"], include_dirs=[pybind11.get_include()])],
    cmdclass={"build_ext": BuildExt},
)
'''


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        return out.exists()

    try:
        import pybind11  # noqa: F401
        import setuptools  # noqa: F401
    except Exception:
        if verbose:
            print(LOG_PREFIX, "pybind11/setuptools unavailable; Python fallback remains usable.", file=sys.stderr)
        return out.exists()

    src_hash = _hash_files([CPP])
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text(encoding="utf-8")).get("hash") == src_hash:
                if verbose:
                    print(LOG_PREFIX, "up to date:", out.name, file=sys.stderr)
                return True
        except Exception:
            pass

    script = BUILD / "_setup_native.py"
    script.write_text(_setup_source(openmp=True), encoding="utf-8")
    ok = _run([sys.executable, str(script), "build_ext", "--inplace"], verbose) and out.exists()

    if not ok:
        # Optimized serial C++ remains a major speedup over the Python O(N^2) kernels.
        script.write_text(_setup_source(openmp=False), encoding="utf-8")
        ok = _run([sys.executable, str(script), "build_ext", "--inplace"], verbose) and out.exists()

    if ok:
        STAMP.write_text(
            json.dumps({"hash": src_hash, "ext": out.name, "python": sys.version}, indent=2),
            encoding="utf-8",
        )
        if verbose:
            print(LOG_PREFIX, "built", out.name, file=sys.stderr)
    return bool(ok)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build 4_SST pybind11 extension if needed.")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ok = build_if_needed(args.force, not args.quiet)
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
