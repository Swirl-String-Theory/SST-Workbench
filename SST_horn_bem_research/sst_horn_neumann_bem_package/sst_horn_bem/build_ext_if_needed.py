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
CPP = ROOT / "cpp" / "horn_bem.cpp"
PKG = ROOT / "sst_horn_bem"
BUILD = ROOT / "build"
STAMP = BUILD / "horn_bem.stamp.json"


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
    return PKG / ("_hornbem" + suffix)


def have_pybind11() -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True)
        return True
    except Exception:
        return False


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print("[sst_horn_bem] building:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode == 0:
        if verbose and proc.stdout.strip():
            print(proc.stdout, file=sys.stderr)
        return True
    if verbose:
        print(f"[sst_horn_bem] build command failed with exit code {proc.returncode}.", file=sys.stderr)
        lines = (proc.stdout + "\n" + proc.stderr).splitlines()
        print("[sst_horn_bem] compiler output tail:", file=sys.stderr)
        print("\n".join(lines[-100:]), file=sys.stderr)
    return False


def _pybind11_includes() -> list[str]:
    return subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True).split()


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


def _direct_compile_commands(compiler: str, out: Path) -> list[list[str]]:
    includes = _pybind11_includes()
    base = [compiler, "-O3", "-std=c++17", "-shared"]
    if platform.system().lower() != "windows":
        base.append("-fPIC")
    common = [*base, *includes, str(CPP), "-o", str(out)]
    cmds = [[*common, *_python_link_args_for_windows()]]
    if platform.system().lower() == "windows":
        cmds.append(common)
    return cmds


def _build_with_setuptools(out: Path, verbose: bool) -> bool:
    try:
        import pybind11  # type: ignore
    except Exception:
        return False
    setup_py = BUILD / "_setup_hornbem.py"
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
        "setup(name='sst_horn_bem_ext', ext_modules=[Extension('sst_horn_bem._hornbem', ['cpp/horn_bem.cpp'], include_dirs=[pybind11.get_include()])], cmdclass={'build_ext': BuildExt})\n",
        encoding="utf-8",
    )
    return _run([sys.executable, str(setup_py), "build_ext", "--inplace"], ROOT, verbose) and out.exists()


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler or not have_pybind11():
        if verbose:
            print("[sst_horn_bem] pybind11/compiler unavailable; using NumPy fallback.", file=sys.stderr)
        return out.exists()
    src_hash = _hash_files([CPP])
    meta = {"hash": src_hash, "python": sys.version, "compiler": compiler, "ext_suffix": out.name, "platform": platform.platform()}
    if not force and out.exists() and STAMP.exists():
        try:
            old = json.loads(STAMP.read_text())
            if old.get("hash") == src_hash and old.get("compiler") == compiler and old.get("ext_suffix") == out.name:
                if verbose:
                    print("[sst_horn_bem] C++ extension is up to date.", file=sys.stderr)
                return True
        except Exception:
            pass
    ok = False
    try:
        for cmd in _direct_compile_commands(compiler, out):
            ok = _run(cmd, ROOT, verbose)
            if ok and out.exists():
                break
    except Exception as exc:
        if verbose:
            print(f"[sst_horn_bem] direct build setup failed: {exc}", file=sys.stderr)
    if not ok:
        ok = _build_with_setuptools(out, verbose)
    if ok and out.exists():
        STAMP.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if verbose:
            print(f"[sst_horn_bem] built {out}", file=sys.stderr)
        return True
    if verbose:
        print("[sst_horn_bem] C++ build unavailable; NumPy fallback remains usable.", file=sys.stderr)
    return out.exists()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ok = build_if_needed(force=args.force, verbose=not args.quiet)
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
