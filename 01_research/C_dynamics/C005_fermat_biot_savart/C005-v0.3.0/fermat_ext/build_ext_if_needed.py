from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.machinery
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from ._config import CPP_DIR_REL, EXT_BASENAME, LOG_PREFIX, PACKAGE_NAME, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[1]
PKG = Path(__file__).resolve().parent
CPP_DIR = ROOT / CPP_DIR_REL
BUILD = ROOT / "build"
STAMP = BUILD / STAMP_BASENAME


def source_files() -> list[Path]:
    return sorted([*CPP_DIR.glob("*.cpp"), *CPP_DIR.glob("*.hpp"), *CPP_DIR.glob("*.h")])


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


def _run(cmd: list[str], cwd: Path, verbose: bool) -> tuple[bool, str]:
    if verbose:
        print(f"{LOG_PREFIX} compile:", " ".join(cmd), file=sys.stderr)
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode != 0 and verbose:
        print("\n".join(log.splitlines()[-60:]), file=sys.stderr)
    return proc.returncode == 0, log


def _build_with_setuptools(verbose: bool) -> tuple[bool, str]:
    try:
        import pybind11  # noqa: F401
    except Exception as exc:
        return False, f"pybind11 unavailable: {exc}"
    BUILD.mkdir(exist_ok=True)
    setup_py = BUILD / f"_setup_{EXT_BASENAME}.py"
    setup_py.write_text(
        "from setuptools import setup, Extension\n"
        "from setuptools.command.build_ext import build_ext\n"
        "import pybind11\n"
        "class BuildExt(build_ext):\n"
        "    def build_extensions(self):\n"
        "        for ext in self.extensions:\n"
        "            ext.extra_compile_args = ['/O2','/std:c++17'] if self.compiler.compiler_type == 'msvc' else ['-O3','-std=c++17']\n"
        "        super().build_extensions()\n"
        f"setup(name='{PACKAGE_NAME}_ext', version='0.3.0', "
        f"packages=['{PACKAGE_NAME}'], package_dir={{'{PACKAGE_NAME}': '{PACKAGE_NAME}'}}, py_modules=[], "
        f"ext_modules=[Extension('{PACKAGE_NAME}.{EXT_BASENAME}', "
        "['cpp/native.cpp'], include_dirs=[pybind11.get_include(), 'cpp'], language='c++')], "
        "cmdclass={'build_ext': BuildExt})\n",
        encoding="utf-8",
    )
    ok, log = _run([sys.executable, str(setup_py), "build_ext", "--inplace"], ROOT, verbose)
    return ok and extension_path().exists(), log


def import_existing() -> tuple[object | None, str | None]:
    try:
        return importlib.import_module(f"{PACKAGE_NAME}.{EXT_BASENAME}"), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def build_if_needed(force: bool = False, verbose: bool = True) -> dict:
    out = extension_path()
    files = source_files()
    BUILD.mkdir(exist_ok=True)
    result = {
        "ok": False,
        "built": False,
        "extension": str(out),
        "source_count": len(files),
        "compiler": None,
        "error": None,
    }
    if not files:
        result["error"] = f"no C++ sources in {CPP_DIR}"
        return result
    try:
        import pybind11  # noqa: F401
    except Exception as exc:
        result["error"] = f"pybind11 unavailable: {exc}"
        result["ok"] = out.exists()
        return result

    compiler = os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    result["compiler"] = compiler
    src_hash = _hash_files(files)
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text(encoding="utf-8")).get("hash") == src_hash:
                result["ok"] = True
                return result
        except Exception:
            pass

    ok, log = _build_with_setuptools(verbose)
    if ok:
        result.update(ok=True, built=True)
        STAMP.write_text(json.dumps({
            "hash": src_hash,
            "compiler": compiler,
            "extension": out.name,
            "python": sys.version,
            "platform": platform.platform(),
            "sources": [str(p.relative_to(ROOT)) for p in files],
        }, indent=2), encoding="utf-8")
    else:
        result["error"] = "\n".join(log.splitlines()[-20:])
        result["ok"] = out.exists()
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the SST Fermat pybind11 extension when sources changed.")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    result = build_if_needed(force=args.force, verbose=not args.quiet)
    print(json.dumps(result, indent=2))
    return 0 if (result["ok"] or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
