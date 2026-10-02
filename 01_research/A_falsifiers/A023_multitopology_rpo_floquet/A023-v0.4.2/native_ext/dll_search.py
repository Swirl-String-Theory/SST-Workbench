from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable

_DLL_HANDLES: list[object] = []
_REGISTERED: set[str] = set()


def _candidate_dirs() -> list[Path]:
    if os.name != "nt":
        return []

    candidates: list[Path] = []

    explicit = os.environ.get("SST_ONEAPI_DLL_DIR")
    if explicit:
        candidates.append(Path(explicit))

    oneapi_root = os.environ.get("ONEAPI_ROOT")
    if oneapi_root:
        root = Path(oneapi_root)
        candidates.extend([
            root / "compiler" / "latest" / "bin",
            root / "tbb" / "latest" / "bin",
            root / "mkl" / "latest" / "bin",
        ])

    # setvars.bat may have placed additional oneAPI runtime directories on PATH.
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        p = Path(entry)
        text = str(p).lower()
        if "intel" in text and "oneapi" in text:
            candidates.append(p)

    out: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        try:
            if not p.is_dir():
                continue
            key = str(p.resolve()).lower()
        except OSError:
            continue
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def configure_windows_dll_search(*, verbose: bool = False) -> list[str]:
    """Register oneAPI DLL directories for CPython extension-module dependencies.

    CPython >=3.8 does not reliably use PATH for dependent DLL resolution of .pyd
    modules.  os.add_dll_directory() returns a handle; the handle must remain alive
    or Windows removes that directory from the process DLL search path.
    """
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return []

    added: list[str] = []
    for p in _candidate_dirs():
        key = str(p.resolve()).lower()
        if key in _REGISTERED:
            continue
        try:
            handle = os.add_dll_directory(str(p))
        except OSError as exc:
            if verbose:
                print(f"[SST-MULTITOPOLOGY-NATIVE] DLL directory rejected: {p}: {exc}", file=sys.stderr)
            continue
        _DLL_HANDLES.append(handle)  # keep alive for the lifetime of the process
        _REGISTERED.add(key)
        added.append(str(p))
        if verbose:
            print(f"[SST-MULTITOPOLOGY-NATIVE] DLL directory registered: {p}", file=sys.stderr)
    return added


def registered_dll_dirs() -> list[str]:
    return sorted(_REGISTERED)
