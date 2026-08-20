from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from .dll_search import configure_windows_dll_search

from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[1]
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


def extension_path() -> Path:
    suffix = sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG / (EXT_BASENAME + suffix)


def _extension_imports(out: Path, verbose: bool = False) -> bool:
    """Validate extension import in an isolated child process.

    A broken SYCL device-image registration can terminate CPython with 0xC0000005
    before Python can raise ImportError.  Never probe an untrusted freshly-built
    SYCL extension in the builder process itself.
    """
    if not out.exists():
        return False
    code = (
        "from native_ext.dll_search import configure_windows_dll_search; "
        "configure_windows_dll_search(verbose=False); "
        "import native_ext._native as n; "
        "print('SST_IMPORT_OK', bool(getattr(n, 'sycl_compiled', False)))"
    )
    env = os.environ.copy()
    # Work around confirmed dynamic-SYCL-library persistent-cache crashes while
    # keeping the scientific computation itself unchanged.
    env.setdefault("SYCL_CACHE_PERSISTENT", "0")
    try:
        cp = subprocess.run(
            [sys.executable, "-X", "faulthandler", "-c", code],
            cwd=str(ROOT), env=env, text=True, capture_output=True, timeout=60
        )
    except Exception as exc:
        if verbose:
            print(f"{LOG_PREFIX} isolated import probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False
    if verbose and cp.stdout.strip():
        print(f"{LOG_PREFIX} import-probe stdout: {cp.stdout.strip()}", file=sys.stderr)
    if cp.returncode != 0:
        if verbose:
            print(f"{LOG_PREFIX} isolated import probe rc={cp.returncode}", file=sys.stderr)
            if cp.stderr.strip():
                print(cp.stderr.rstrip(), file=sys.stderr)
        return False
    return "SST_IMPORT_OK" in cp.stdout


def have_pybind11() -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True)
        return True
    except Exception:
        return False


def sycl_disabled() -> bool:
    return os.environ.get("SST_DISABLE_SYCL", "0") == "1"


def openmp_disabled() -> bool:
    return os.environ.get("SST_DISABLE_OPENMP", "0") == "1"


def _run(cmd: list[str], cwd: Path, verbose: bool) -> bool:
    if verbose:
        print(f"{LOG_PREFIX} compile:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode == 0:
        return True
    if verbose:
        print(f"{LOG_PREFIX} build failed: {proc.returncode}", file=sys.stderr)
        tail = (proc.stdout + "\n" + proc.stderr).splitlines()[-40:]
        print("\n".join(tail), file=sys.stderr)
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


def _python_msvc_lib() -> Path | None:
    maj, minor = sys.version_info[:2]
    name = f"python{maj}{minor}.lib"
    for d in _candidate_python_lib_dirs():
        p = d / name
        if p.exists():
            return p
    return None


def _python_link_args_for_windows(*, icpx: bool = False) -> list[str]:
    if platform.system().lower() != "windows":
        return []
    maj, minor = sys.version_info[:2]
    lib = _python_msvc_lib()
    if icpx:
        return [str(lib)] if lib is not None else []
    args: list[str] = []
    if lib is not None:
        args.append(str(lib))
    for d in _candidate_python_lib_dirs():
        args.append("-L" + str(d))
    args.extend([f"-lpython{maj}{minor}"])
    return args


def _pybind_includes() -> list[str]:
    return subprocess.check_output([sys.executable, "-m", "pybind11", "--includes"], text=True).split()


def _python_include_flags() -> list[str]:
    inc = sysconfig.get_path("include")
    flags = [f"-I{inc}"] if inc else []
    plat = sysconfig.get_path("platinclude")
    if plat and plat != inc:
        flags.append(f"-I{plat}")
    return flags


def find_icpx() -> Path | None:
    env_cxx = os.environ.get("CXX") or os.environ.get("ICPX")
    if env_cxx:
        p = Path(env_cxx)
        if p.exists():
            return p
        w = shutil.which(env_cxx)
        if w:
            return Path(w)
    for name in ("icpx", "icx"):
        w = shutil.which(name)
        if w:
            return Path(w)
    roots = [
        Path(r"C:\Program Files (x86)\Intel\oneAPI\compiler\latest\bin"),
        Path(r"C:\Program Files (x86)\Intel\oneAPI\compiler\latest\windows\bin"),
        Path(r"C:\Program Files\Intel\oneAPI\compiler\latest\bin"),
    ]
    for root in roots:
        for name in ("icpx.exe", "icx.exe", "icpx", "icx"):
            cand = root / name
            if cand.exists():
                return cand
    return None


def _windows_oneapi_link_env_ready() -> bool:
    """Return True when Windows LINK can resolve Intel runtime libraries.

    Discovering icpx.exe by absolute path is not sufficient on Windows: the
    Intel oneAPI setvars environment must populate LIB (including libmmd.lib).
    """
    if platform.system().lower() != "windows":
        return True
    lib_env = os.environ.get("LIB", "")
    for raw in lib_env.split(";"):
        raw = raw.strip().strip('"')
        if not raw:
            continue
        try:
            if (Path(raw) / "libmmd.lib").exists():
                return True
        except OSError:
            pass
    return False


def _build_sycl(out: Path, verbose: bool) -> bool:
    if sycl_disabled():
        if verbose:
            print(f"{LOG_PREFIX} SST_DISABLE_SYCL=1; skipping icpx.", file=sys.stderr)
        return False
    icpx = find_icpx()
    if icpx is None:
        if verbose:
            print(f"{LOG_PREFIX} icpx/icx not found; skipping SYCL build.", file=sys.stderr)
        return False
    if not _windows_oneapi_link_env_ready():
        if verbose:
            print(
                f"{LOG_PREFIX} oneAPI compiler found, but Windows oneAPI LIB environment is not initialized "
                "(libmmd.lib not resolvable). Call Intel oneAPI setvars.bat or use run_gpu_sycl.cmd; "
                "skipping SYCL build.",
                file=sys.stderr,
            )
        return False
    if not have_pybind11():
        return False
    includes = _pybind_includes() + _python_include_flags()
    windows = platform.system().lower() == "windows"
    variants: list[list[str]] = []
    common = [str(icpx), "-fsycl", "-fsycl-device-code-split=per_kernel", "-O3", "-std=c++17", "-DSST_HAVE_SYCL", *includes, str(CPP)]
    if windows:
        variants.append([*common, "-shared", "-o", str(out), *_python_link_args_for_windows(icpx=True)])
        variants.append([*common, "-fiopenmp", "-shared", "-o", str(out), *_python_link_args_for_windows(icpx=True)])
        variants.append(
            [
                str(icpx),
                "-fsycl",
                "-fsycl-device-code-split=per_kernel",
                "-O2",
                "-std=c++17",
                "-shared",
                "-DSST_HAVE_SYCL",
                *includes,
                str(CPP),
                "-o",
                str(out),
                *_python_link_args_for_windows(icpx=True),
            ]
        )
    else:
        variants.append([*common, "-shared", "-fPIC", "-o", str(out), "-fopenmp"])
        variants.append([*common, "-shared", "-fPIC", "-o", str(out)])
    for cmd in variants:
        if _run(cmd, ROOT, verbose) and out.exists():
            return True
    return False


def _build_with_setuptools(out: Path, verbose: bool, openmp: bool = True) -> bool:
    try:
        import pybind11  # type: ignore  # noqa: F401
    except Exception:
        return False
    if openmp and openmp_disabled():
        openmp = False
    setup_py = BUILD / f"_setup_{EXT_BASENAME}.py"
    setup_py.write_text(
        "from setuptools import setup, Extension\n"
        "from setuptools.command.build_ext import build_ext\n"
        "import pybind11\n"
        "class BuildExt(build_ext):\n"
        "    def build_extensions(self):\n"
        "        for ext in self.extensions:\n"
        "            if self.compiler.compiler_type == 'msvc':\n"
        "                ext.extra_compile_args = ['/O2', '/std:c++17'] + "
        f"(['/openmp'] if {openmp!r} else [])\n"
        "            else:\n"
        "                ext.extra_compile_args = ['-O3', '-std=c++17'] + "
        f"(['-fopenmp'] if {openmp!r} else [])\n"
        f"                ext.extra_link_args = (['-fopenmp'] if {openmp!r} else [])\n"
        "        super().build_extensions()\n"
        f"setup(name='{PKG.name}_ext', ext_modules=[Extension('{PKG.name}.{EXT_BASENAME}', "
        f"['{CPP_REL.as_posix()}'], include_dirs=[pybind11.get_include()])], "
        "cmdclass={'build_ext': BuildExt})\n",
        encoding="utf-8",
    )
    return _run([sys.executable, str(setup_py), "build_ext", "--inplace"], ROOT, verbose) and out.exists()


def build_if_needed(force: bool = False, verbose: bool = True, require_sycl: bool = False) -> bool:
    out = extension_path()
    BUILD.mkdir(exist_ok=True)

    if not CPP.exists():
        if verbose:
            print(f"{LOG_PREFIX} missing source: {CPP}", file=sys.stderr)
        return out.exists()

    if not have_pybind11():
        if verbose:
            print(f"{LOG_PREFIX} pybind11 unavailable; using Python fallback.", file=sys.stderr)
        return out.exists()

    src_hash = _hash_files([CPP])
    compiler = str(find_icpx() or os.environ.get("CXX") or shutil.which("c++") or "msvc")
    meta = {"hash": src_hash, "compiler": compiler, "ext": out.name, "cpp": str(CPP_REL)}
    if not force and out.exists() and STAMP.exists():
        try:
            prev = json.loads(STAMP.read_text(encoding="utf-8"))
            if prev.get("hash") == src_hash and _extension_imports(out, verbose=verbose):
                if verbose:
                    print(f"{LOG_PREFIX} up to date: {out.name} backend={prev.get('backend')}", file=sys.stderr)
                return True
        except Exception:
            pass

    backend = "serial"
    ok = _build_sycl(out, verbose)
    if ok and not _extension_imports(out, verbose=verbose):
        if verbose:
            print(
                f"{LOG_PREFIX} SYCL module built but failed to load (oneAPI DLLs?). "
                "Call setvars.bat / run_arc.cmd, or falling back to OpenMP.",
                file=sys.stderr,
            )
        # Preserve the failed-load binary.  It is valuable for dumpbin/Dependencies
        # diagnostics and may load successfully once the Python DLL search path is fixed.
        ok = False
    if ok:
        backend = "sycl"
    elif require_sycl:
        if verbose:
            print(f"{LOG_PREFIX} required SYCL build/load failed; host fallback intentionally disabled.", file=sys.stderr)
        return False
    else:
        windows = platform.system().lower() == "windows"
        if windows:
            ok = _build_with_setuptools(out, verbose, openmp=not openmp_disabled())
            if not ok:
                ok = _build_with_setuptools(out, verbose, openmp=False)
        else:
            compiler_bin = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
            if compiler_bin:
                includes = _pybind_includes()
                base = [compiler_bin, "-O3", "-std=c++17", "-shared", "-fPIC", *includes, str(CPP), "-o", str(out)]
                if not openmp_disabled():
                    ok = _run([*base, "-fopenmp"], ROOT, verbose) and out.exists()
                if not ok:
                    ok = _run(base, ROOT, verbose) and out.exists()
            if not ok:
                ok = _build_with_setuptools(out, verbose, openmp=not openmp_disabled())
            if not ok:
                ok = _build_with_setuptools(out, verbose, openmp=False)
        if ok:
            backend = "openmp" if not openmp_disabled() else "serial"

    if ok and out.exists():
        meta["backend"] = backend
        STAMP.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        if verbose:
            print(f"{LOG_PREFIX} built {out.name} backend={backend}", file=sys.stderr)
        return True

    if verbose:
        print(f"{LOG_PREFIX} C++ build failed; Python fallback remains usable.", file=sys.stderr)
    return out.exists()


def main() -> int:
    ap = argparse.ArgumentParser(description="Build SYCL/OpenMP pybind11 extension if C++ sources changed.")
    ap.add_argument("--force", action="store_true", help="Rebuild even when stamp hash matches.")
    ap.add_argument("--quiet", action="store_true", help="Suppress build log output.")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when extension is missing after build attempt.",
    )
    ap.add_argument(
        "--require-sycl",
        action="store_true",
        help="Require a genuine SYCL build/load; do not silently fall back to OpenMP/serial.",
    )
    args = ap.parse_args()
    ok = build_if_needed(force=args.force, verbose=not args.quiet, require_sycl=args.require_sycl)
    return 0 if (ok or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
