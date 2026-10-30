from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from ._config import EXT_BASENAME, LOG_PREFIX, PACKAGE_NAME, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
STAMP = BUILD / STAMP_BASENAME
_DLL_HANDLES: list[object] = []
_ACTIVE_DIRS: list[str] = []

_RUNTIME_DLL_NAMES = (
    "libstdc++-6.dll",
    "libgcc_s_seh-1.dll",
    "libgcc_s_sjlj-1.dll",
    "libgcc_s_dw2-1.dll",
    "libwinpthread-1.dll",
)


def _dedupe_existing_dirs(paths: Iterable[Path | str]) -> list[Path]:
    out: list[Path] = []
    seen: set[str] = set()
    for raw in paths:
        try:
            p = Path(raw).expanduser().resolve()
        except Exception:
            continue
        if not p.is_dir():
            continue
        key = os.path.normcase(str(p))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _compiler_candidates_from_stamp() -> tuple[str | None, list[Path]]:
    compiler = None
    dirs: list[Path] = []
    if STAMP.exists():
        try:
            data = json.loads(STAMP.read_text(encoding="utf-8"))
            compiler = data.get("compiler") or None
            for d in data.get("runtime_dll_dirs", []) or []:
                dirs.append(Path(d))
        except Exception:
            pass
    return compiler, dirs


def _resolve_compiler() -> str | None:
    stamped, _ = _compiler_candidates_from_stamp()
    for candidate in (stamped, os.environ.get("CXX"), shutil.which("c++"), shutil.which("g++")):
        if candidate and Path(candidate).exists():
            return str(Path(candidate).resolve())
    return None


def compiler_runtime_dirs(compiler: str | None = None) -> list[Path]:
    if platform.system().lower() != "windows":
        return []
    compiler = compiler or _resolve_compiler()
    _, stamped_dirs = _compiler_candidates_from_stamp()
    paths: list[Path | str] = list(stamped_dirs)
    env_dir = os.environ.get("FINITE_CORE_SPECTRAL_DLL_DIR")
    if env_dir:
        paths.extend(x for x in env_dir.split(os.pathsep) if x)
    if compiler:
        cp = Path(compiler).resolve()
        paths.append(cp.parent)
        for name in _RUNTIME_DLL_NAMES:
            try:
                out = subprocess.check_output(
                    [str(cp), f"-print-file-name={name}"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
            except Exception:
                continue
            if out and out != name:
                fp = Path(out)
                if fp.exists():
                    paths.append(fp.resolve().parent)
    return _dedupe_existing_dirs(paths)


def runtime_dependency_report(compiler: str | None = None) -> dict:
    compiler = compiler or _resolve_compiler()
    dirs = compiler_runtime_dirs(compiler)
    found: dict[str, str | None] = {}
    for name in _RUNTIME_DLL_NAMES:
        hit = next((d / name for d in dirs if (d / name).exists()), None)
        found[name] = str(hit) if hit else None
    return {
        "platform": platform.system(),
        "python_executable": sys.executable,
        "compiler": compiler,
        "runtime_dll_dirs": [str(d) for d in dirs],
        "runtime_dlls": found,
    }


def activate_runtime_dll_dirs(verbose: bool = False) -> list[str]:
    """Add MinGW/Strawberry runtime locations to Windows' extension DLL search path.

    Handles returned by ``os.add_dll_directory`` are intentionally retained for
    the process lifetime; closing them would remove the directory again.
    """
    if platform.system().lower() != "windows":
        return []
    for d in compiler_runtime_dirs():
        s = str(d)
        key = os.path.normcase(s)
        if any(os.path.normcase(x) == key for x in _ACTIVE_DIRS):
            continue
        try:
            handle = os.add_dll_directory(s)
        except (AttributeError, FileNotFoundError, OSError) as exc:
            if verbose:
                print(f"{LOG_PREFIX} DLL directory skipped: {s}: {exc}", file=sys.stderr)
            continue
        _DLL_HANDLES.append(handle)
        _ACTIVE_DIRS.append(s)
        if verbose:
            print(f"{LOG_PREFIX} DLL directory active: {s}", file=sys.stderr)
    return list(_ACTIVE_DIRS)


def import_native(verbose: bool = False):
    active = activate_runtime_dll_dirs(verbose=verbose)
    try:
        mod = importlib.import_module(f"{PACKAGE_NAME}.{EXT_BASENAME}")
        return mod, {"ok": True, "active_dll_dirs": active, **runtime_dependency_report()}
    except Exception as exc:
        report = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "active_dll_dirs": active, **runtime_dependency_report()}
        if verbose:
            print(f"{LOG_PREFIX} native import failed: {report['error']}", file=sys.stderr)
            print(json.dumps(report, indent=2), file=sys.stderr)
        return None, report


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Windows runtime DLL resolution and import the native extension.")
    ap.add_argument("--strict", action="store_true", help="Return exit code 1 if native import fails.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    _, report = import_native(verbose=not args.quiet)
    print(json.dumps(report, indent=2))
    return 0 if (report["ok"] or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
