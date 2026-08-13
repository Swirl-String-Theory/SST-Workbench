from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, PACKAGE_NAME, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
CPP = ROOT / CPP_REL
BUILD = ROOT / "build"
STAMP = BUILD / STAMP_BASENAME


def _hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def source_hash() -> str:
    return _hash_files([CPP]) if CPP.exists() else ""


def extension_path() -> Path:
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG / (EXT_BASENAME + suffix)


def _python_include_dirs() -> list[Path]:
    dirs: list[Path] = []
    for key in ("include", "platinclude"):
        value = sysconfig.get_paths().get(key)
        if value:
            dirs.append(Path(value))
    return _dedupe_existing(dirs)


def _dedupe_existing(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            out.append(path)
    return out


def pybind_include_dirs() -> list[Path]:
    candidates: list[Path] = []
    try:
        import pybind11  # type: ignore
        candidates.extend([Path(pybind11.get_include()), Path(pybind11.get_include(user=True))])
    except Exception:
        pass

    # A number of scientific Python distributions vendor the unmodified pybind11 headers.
    try:
        import torch  # type: ignore
        candidates.append(Path(torch.__file__).resolve().parent / "include")
    except Exception:
        pass

    for prefix in map(Path, sys.path):
        candidates.extend([
            prefix / "pybind11" / "include",
            prefix / "torch" / "include",
        ])
    candidates.extend([Path("/usr/include"), Path("/usr/local/include")])
    candidates = _dedupe_existing(candidates)
    return [path for path in candidates if (path / "pybind11" / "pybind11.h").exists()]


def have_headers() -> bool:
    return bool(pybind_include_dirs())


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print(f"{LOG_PREFIX} compile:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode == 0:
        return True
    if verbose:
        print(f"{LOG_PREFIX} build failed: {proc.returncode}", file=sys.stderr)
        tail = (proc.stdout + "\n" + proc.stderr).splitlines()[-80:]
        print("\n".join(tail), file=sys.stderr)
    return False


def _openmp_flags(compiler: str) -> tuple[list[str], list[str]]:
    name = Path(compiler).name.lower()
    if platform.system().lower() == "windows" and ("cl" in name or "msvc" in name):
        return ["/openmp"], []
    return ["-fopenmp"], ["-fopenmp"]


def _build_direct(out: Path, verbose: bool, use_openmp: bool) -> bool:
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        return False
    if platform.system().lower() == "windows":
        return False
    compile_flags = ["-O3", "-std=c++17", "-shared", "-fPIC"]
    link_flags: list[str] = []
    if use_openmp:
        omp_compile, omp_link = _openmp_flags(compiler)
        compile_flags += omp_compile
        link_flags += omp_link
    includes = [f"-I{path}" for path in [*_python_include_dirs(), *pybind_include_dirs()]]
    cmd = [compiler, *compile_flags, *includes, str(CPP), "-o", str(out), *link_flags]
    return _run(cmd, ROOT, verbose) and out.exists()


def _build_with_setuptools(out: Path, verbose: bool, use_openmp: bool) -> bool:
    include_dirs = [str(path) for path in [*_python_include_dirs(), *pybind_include_dirs()]]
    if not include_dirs:
        return False
    setup_py = BUILD / f"_setup_{EXT_BASENAME}.py"
    omp_compile = []
    omp_link = []
    if use_openmp:
        omp_compile = ["/openmp"] if platform.system().lower() == "windows" else ["-fopenmp"]
        omp_link = [] if platform.system().lower() == "windows" else ["-fopenmp"]
    setup_py.write_text(
        "from setuptools import setup, Extension\n"
        "from setuptools.command.build_ext import build_ext\n"
        "class BuildExt(build_ext):\n"
        "    def build_extensions(self):\n"
        "        for ext in self.extensions:\n"
        "            if self.compiler.compiler_type == 'msvc':\n"
        f"                ext.extra_compile_args = ['/O2', '/std:c++17'] + {omp_compile!r}\n"
        "            else:\n"
        f"                ext.extra_compile_args = ['-O3', '-std=c++17'] + {omp_compile!r}\n"
        f"                ext.extra_link_args = {omp_link!r}\n"
        "        super().build_extensions()\n"
        f"setup(name='sst_ideal_links_native', package_dir={{'': 'src'}}, "
        f"ext_modules=[Extension('{PACKAGE_NAME}.{EXT_BASENAME}', ['{CPP_REL.as_posix()}'], "
        f"include_dirs={include_dirs!r}, language='c++')], cmdclass={{'build_ext': BuildExt}})\n",
        encoding="utf-8",
    )
    return _run([sys.executable, str(setup_py), "build_ext", "--inplace"], ROOT, verbose) and out.exists()


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        if verbose:
            print(f"{LOG_PREFIX} missing source: {CPP}", file=sys.stderr)
        return out.exists()
    if not have_headers():
        if verbose:
            print(f"{LOG_PREFIX} pybind11 headers unavailable; Python fallback remains usable.", file=sys.stderr)
        return out.exists()

    src_hash = source_hash()
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++") or "setuptools"
    meta = {
        "hash": src_hash,
        "compiler": compiler,
        "extension": out.name,
        "cpp": str(CPP_REL),
        "python": sys.version,
        "platform": platform.platform(),
    }
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text(encoding="utf-8")).get("hash") == src_hash:
                if verbose:
                    print(f"{LOG_PREFIX} up to date: {out.name}", file=sys.stderr)
                return True
        except Exception:
            pass

    if out.exists():
        out.unlink()
    ok = _build_direct(out, verbose, use_openmp=True)
    if not ok:
        ok = _build_with_setuptools(out, verbose, use_openmp=True)
    if not ok:
        if verbose:
            print(f"{LOG_PREFIX} retrying without OpenMP", file=sys.stderr)
        ok = _build_direct(out, verbose, use_openmp=False)
    if not ok:
        ok = _build_with_setuptools(out, verbose, use_openmp=False)

    if ok and out.exists():
        STAMP.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if verbose:
            print(f"{LOG_PREFIX} built {out.name}", file=sys.stderr)
        return True
    if verbose:
        print(f"{LOG_PREFIX} C++ build failed; Python fallback remains usable.", file=sys.stderr)
    return out.exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the SST ideal-link pybind11 extension.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    ok = build_if_needed(force=args.force, verbose=not args.quiet)
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
