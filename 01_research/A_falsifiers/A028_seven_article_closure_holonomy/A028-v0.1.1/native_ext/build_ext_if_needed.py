from __future__ import annotations

from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _import_native():
    importlib.invalidate_caches()
    return importlib.import_module("native_ext._native")


def _build(openmp: bool) -> None:
    setup = ROOT / "build" / "_setup_native.py"
    env = os.environ.copy()
    env["SST_NATIVE_OPENMP"] = "1" if openmp else "0"
    mode = "OpenMP" if openmp else "serial fallback"
    cmd = [sys.executable, str(setup), "build_ext", "--inplace", "--force"]
    print(f"[SST7-NATIVE] building ({mode}):", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT, env=env)


try:
    mod = _import_native()
    print(f"[SST7-NATIVE] already built; OpenMP={bool(getattr(mod, 'openmp', False))}")
except Exception as first_import_error:
    want_openmp = os.environ.get("SST_NATIVE_OPENMP", "1") != "0"
    try:
        _build(want_openmp)
    except subprocess.CalledProcessError:
        # Compilation should remain usable on systems where an OpenMP toolchain is
        # unavailable.  If OpenMP was requested, retry the identical C++17 kernels
        # without OpenMP.  A genuine C++ syntax error will fail both attempts.
        if not want_openmp:
            raise
        print("[SST7-NATIVE] OpenMP build failed; retrying without OpenMP...")
        _build(False)

    try:
        mod = _import_native()
    except Exception as second_import_error:
        raise RuntimeError(
            "Native extension was compiled but could not be imported. "
            f"Initial import error: {first_import_error!r}; "
            f"post-build import error: {second_import_error!r}"
        ) from second_import_error

    print(f"[SST7-NATIVE] build complete; OpenMP={bool(getattr(mod, 'openmp', False))}")
