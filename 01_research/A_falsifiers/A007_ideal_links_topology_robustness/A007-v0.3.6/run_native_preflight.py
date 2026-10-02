#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib, json, platform, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from sst_link_suite.native_ext.build_ext_if_needed import (
    build_if_needed, extension_path, have_headers, pybind_include_dirs, source_hash,
)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and import the ABI-specific SST pybind11 extension with full diagnostics."
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    report = {
        "ok": False,
        "interpreter": sys.executable,
        "python": sys.version,
        "platform": platform.platform(),
        "source_hash": source_hash(),
        "extension_path": str(extension_path()),
        "extension_exists_before": extension_path().exists(),
        "pybind11_headers_found": have_headers(),
        "pybind11_include_dirs": [str(p) for p in pybind_include_dirs()],
    }
    try:
        import pybind11
        report["pybind11"] = getattr(pybind11, "__version__", "unknown")
    except Exception as exc:
        report["pybind11_error"] = f"{type(exc).__name__}: {exc}"
    try:
        import setuptools
        report["setuptools"] = getattr(setuptools, "__version__", "unknown")
    except Exception as exc:
        report["setuptools_error"] = f"{type(exc).__name__}: {exc}"
    try:
        print("[native-preflight] interpreter:", sys.executable, flush=True)
        built = build_if_needed(force=args.force, verbose=True)
        report["build_returned"] = bool(built)
        report["extension_exists_after"] = extension_path().exists()
        if not built:
            raise RuntimeError("build_if_needed returned False")
        importlib.invalidate_caches()
        module = importlib.import_module("sst_link_suite.native_ext._native")
        report["build_info"] = dict(module.build_info())
        report["ok"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
