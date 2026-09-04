from __future__ import annotations

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
CPP = ROOT / "cpp" / "hornkernels.cpp"
PKG = ROOT / "sst_horn"
BUILD = ROOT / "build"
STAMP = BUILD / "hornkernels.stamp.json"


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
    return PKG / ("_hornkernels" + suffix)


def have_pybind11() -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True)
        return True
    except Exception:
        return False


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print("[sst_horn] building:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode == 0:
        if verbose and proc.stdout.strip():
            print(proc.stdout, file=sys.stderr)
        return True
    if verbose:
        print(f"[sst_horn] build command failed with exit code {proc.returncode}.", file=sys.stderr)
        # Link failures from pybind11/MinGW can be thousands of lines; keep it readable.
        lines = (proc.stdout + "\n" + proc.stderr).splitlines()
        tail = lines[-80:]
        print("[sst_horn] compiler output tail:", file=sys.stderr)
        print("\n".join(tail), file=sys.stderr)
    return False


def _pybind11_includes() -> list[str]:
    return subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True).split()


def _candidate_python_lib_dirs() -> list[Path]:
    candidates: list[Path] = []
    keys = ["LIBDIR", "LIBPL", "installed_base", "base", "prefix", "exec_prefix"]
    for key in keys:
        val = sysconfig.get_config_var(key)
        if val:
            p = Path(str(val))
            candidates.extend([p, p / "libs", p / "Libs"])
    for p in [Path(sys.base_prefix), Path(sys.prefix), Path(sys.executable).resolve().parents[1]]:
        candidates.extend([p, p / "libs", p / "Libs"])
    # Preserve order but remove duplicates/nonexistent later.
    out: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        try:
            rp = str(p.resolve())
        except Exception:
            rp = str(p)
        if rp not in seen and p.exists():
            seen.add(rp)
            out.append(p)
    return out


def _python_link_args_for_windows() -> list[str]:
    """Return linker args needed by MinGW/clang on Windows.

    CPython extension modules on POSIX commonly leave Python symbols unresolved;
    Windows does not.  A direct g++/clang++ pybind11 build must link against the
    CPython import library or DLL.  The official pybind11 one-liner does not add
    this automatically, which causes errors such as undefined reference to
    `__imp_PyGILState_Check`.
    """
    if platform.system().lower() != "windows":
        return []
    maj, minor = sys.version_info[:2]
    names = [
        f"python{maj}{minor}",
        f"python{maj}.{minor}",
    ]
    args: list[str] = []
    for d in _candidate_python_lib_dirs():
        # -L accepts normal Windows paths for MinGW and clang.
        args.append("-L" + str(d))
    for name in names:
        args.append("-l" + name)
    return args


def _direct_compile_commands(compiler: str, out: Path) -> list[list[str]]:
    includes = _pybind11_includes()
    base = [compiler, "-O3", "-std=c++17", "-shared"]
    if platform.system().lower() != "windows":
        base.append("-fPIC")
    common = [*base, *includes, str(CPP), "-o", str(out)]
    cmds = []
    # On Windows try the Python link args first; on POSIX this is the normal pybind11 command.
    cmds.append([*common, *_python_link_args_for_windows()])
    # Second chance: raw command, useful for Linux/macOS or unusual toolchains.
    if platform.system().lower() == "windows":
        cmds.append(common)
    return cmds


def _build_with_setuptools(out: Path, verbose: bool) -> bool:
    """Try a setuptools build_ext in-place build.

    This path delegates platform-specific Python library/link flags to Python's
    build machinery.  It is often more robust on Windows than hand-written g++
    commands, provided a compatible compiler is installed.
    """
    try:
        import pybind11  # type: ignore
        from setuptools import Extension, setup  # type: ignore
        from setuptools.command.build_ext import build_ext  # type: ignore
    except Exception:
        return False

    class QuietBuildExt(build_ext):
        def build_extensions(self):  # type: ignore[override]
            for ext in self.extensions:
                ext.extra_compile_args = ["-O3", "-std=c++17"] if self.compiler.compiler_type != "msvc" else ["/O2", "/std:c++17"]
            super().build_extensions()

    setup_py = BUILD / "_setup_hornkernels.py"
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
        "setup(name='sst_horn_ext', ext_modules=[Extension('sst_horn._hornkernels', ['cpp/hornkernels.cpp'], include_dirs=[pybind11.get_include()])], cmdclass={'build_ext': BuildExt})\n"
    )
    cmd = [sys.executable, str(setup_py), "build_ext", "--inplace"]
    ok = _run(cmd, ROOT, verbose)
    return ok and out.exists()


def build_if_needed(force: bool = False, verbose: bool = True) -> bool:
    """Build the pybind11 extension only if C++ source or build metadata changed.

    Returns True if a compiled extension is present after the call, False otherwise.
    If pybind11 or a compiler is unavailable, or if linking fails, no exception is
    raised; callers should use the NumPy fallback backend.
    """
    out = extension_path()
    BUILD.mkdir(exist_ok=True)
    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler or not have_pybind11():
        if verbose:
            print("[sst_horn] pybind11 or C++ compiler unavailable; using NumPy fallback.", file=sys.stderr)
        return out.exists()

    src_hash = _hash_files([CPP])
    meta = {
        "hash": src_hash,
        "python": sys.version,
        "compiler": compiler,
        "ext_suffix": out.name,
        "platform": platform.platform(),
    }
    if not force and out.exists() and STAMP.exists():
        try:
            old = json.loads(STAMP.read_text())
            if old.get("hash") == src_hash and old.get("compiler") == compiler and old.get("ext_suffix") == out.name:
                if verbose:
                    print("[sst_horn] C++ extension is up to date.", file=sys.stderr)
                return True
        except Exception:
            pass

    ok = False
    # Prefer direct compilation; if Windows linking needs Python libs, args are included.
    try:
        for cmd in _direct_compile_commands(compiler, out):
            ok = _run(cmd, ROOT, verbose)
            if ok and out.exists():
                break
    except Exception as exc:
        if verbose:
            print(f"[sst_horn] direct build setup failed: {exc}", file=sys.stderr)
        ok = False

    # Fall back to setuptools, which may know the right compiler/linker better.
    if not (ok and out.exists()):
        if verbose:
            print("[sst_horn] trying setuptools build_ext fallback...", file=sys.stderr)
        try:
            ok = _build_with_setuptools(out, verbose)
        except Exception as exc:
            if verbose:
                print(f"[sst_horn] setuptools build failed: {exc}", file=sys.stderr)
            ok = False

    if ok and out.exists():
        STAMP.write_text(json.dumps(meta, indent=2))
        return True

    if verbose:
        print("[sst_horn] C++ extension unavailable; using NumPy fallback backend.", file=sys.stderr)
    return False


if __name__ == "__main__":
    strict = "--strict" in sys.argv or os.environ.get("SST_HORN_BUILD_STRICT") == "1"
    ok = build_if_needed(force="--force" in sys.argv)
    # Default exit is success because the package has a supported NumPy fallback.
    raise SystemExit(0 if ok or not strict else 1)
