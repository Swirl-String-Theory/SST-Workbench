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

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "cpp" / "ssdl_bem.cpp"
PKG = ROOT / "sst_ssdl_audit"
BUILD = ROOT / "build"
STAMP = BUILD / "ssdl_bem.stamp.json"


def _hash_files(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def extension_path() -> Path:
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG / ("_ssdlbem" + suffix)


def have_pybind11() -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True)
        return True
    except Exception:
        return False


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print("[sst_ssdl_audit] compile:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode == 0:
        return True
    if verbose:
        print(f"[sst_ssdl_audit] build failed: {proc.returncode}", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
    return False


def _candidate_python_lib_dirs() -> list[Path]:
    candidates: list[Path] = []
    for key in ["LIBDIR", "LIBPL", "installed_base", "base", "prefix", "exec_prefix"]:
        val = sysconfig.get_config_var(key)
        if val:
            p = Path(str(val))
            candidates.extend([p, p / "libs", p / "Libs"])
    for p in [Path(sys.base_prefix), Path(sys.prefix), Path(sys.executable).resolve().parents[1]]:
        candidates.extend([p, p / "libs", p / "Libs"])
    out: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        if not p.exists():
            continue
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out


def _python_link_args_for_windows() -> list[str]:
    if platform.system().lower() != "windows":
        return []
    maj, minor = sys.version_info[:2]
    args: list[str] = []
    for d in _candidate_python_lib_dirs():
        args.append("-L" + str(d))
    args.extend([f"-lpython{maj}{minor}", f"-lpython{maj}.{minor}"])
    return args


def _build_with_setuptools(out: Path, verbose: bool) -> bool:
    try:
        import pybind11  # type: ignore
    except Exception:
        return False
    setup_py = BUILD / "_setup_ssdlbem.py"
    setup_py.write_text(
        "from setuptools import setup, Extension\n"
        "from setuptools.command.build_ext import build_ext\n"
        "import pybind11\n"
        "class BuildExt(build_ext):\n"
        "    def build_extensions(self):\n"
        "        for ext in self.extensions:\n"
        "            if self.compiler.compiler_type == 'msvc':\n"
        "                ext.extra_compile_args = ['/O2', '/std:c++17']\n"
        "            else:\n"
        "                ext.extra_compile_args = ['-O3', '-std=c++17']\n"
        "        super().build_extensions()\n"
        "setup(name='sst_ssdl_audit_ext', ext_modules=[Extension('sst_ssdl_audit._ssdlbem', "
        "['cpp/ssdl_bem.cpp'], include_dirs=[pybind11.get_include()])], "
        "cmdclass={'build_ext': BuildExt})\n",
        encoding="utf-8",
    )
    return _run([sys.executable, str(setup_py), "build_ext", "--inplace"], ROOT, verbose) and out.exists()


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler or not have_pybind11():
        return out.exists()

    src_hash = _hash_files([CPP])
    meta = {"hash": src_hash, "compiler": compiler, "ext": out.name}
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get("hash") == src_hash:
                return True
        except Exception:
            pass

    includes = subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True).split()
    base = [compiler, "-O3", "-std=c++17", "-shared"]
    if platform.system().lower() != "windows":
        base.append("-fPIC")
    cmd = [*base, *includes, str(CPP), "-o", str(out), *_python_link_args_for_windows()]

    ok = _run(cmd, ROOT, verbose) and out.exists()
    if not ok:
        ok = _build_with_setuptools(out, verbose)

    if ok and out.exists():
        STAMP.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return True
    return out.exists()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    build_if_needed(ap.parse_args().force)
