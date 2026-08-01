"""Build helper for local SST chi-phase v5 pybind11 extension.
Windows-safe: relative source path + short build-temp to avoid MSVC object path issues.
"""
from __future__ import annotations
import glob, os, sys
from typing import Optional
MODULE_NAME = "sst_chi_phase_v5"
CPP_FILENAME = "sst_chi_phase_v5.cpp"
def base_dir(script_dir: Optional[str] = None) -> str:
    return script_dir or os.path.dirname(os.path.abspath(__file__))
def needs_recompile(script_dir: Optional[str] = None) -> bool:
    base = base_dir(script_dir); src = os.path.join(base, CPP_FILENAME)
    if not os.path.exists(src): return False
    binaries = [f for f in glob.glob(os.path.join(base, f"{MODULE_NAME}.*")) if f.endswith(".pyd") or f.endswith(".so")]
    if not binaries: return True
    latest_binary = max(binaries, key=os.path.getmtime)
    return os.path.getmtime(src) > os.path.getmtime(latest_binary)
def build_module(script_dir: Optional[str] = None):
    try:
        import pybind11
    except ImportError as exc:
        raise ImportError("pybind11 is not installed. Run `pip install pybind11`, or use --python fallback.") from exc
    from setuptools import Extension, setup
    base = base_dir(script_dir)
    print(f"[*] Building {MODULE_NAME} C++ module via pybind11...")
    c_args = ["/O2", "/std:c++14"] if os.name == "nt" else ["-O3", "-std=c++14"]
    ext_modules = [Extension(MODULE_NAME, [CPP_FILENAME], include_dirs=[pybind11.get_include()], language="c++", extra_compile_args=c_args)]
    old_cwd = os.getcwd(); old_argv = list(sys.argv)
    try:
        os.chdir(base); sys.argv = ["setup.py", "build_ext", "--inplace", "--build-temp", "_build_tmp"]
        setup(name=MODULE_NAME, ext_modules=ext_modules, script_args=["build_ext", "--inplace", "--build-temp", "_build_tmp"])
    finally:
        os.chdir(old_cwd); sys.argv = old_argv
def import_module(*, auto_build: bool = True, script_dir: Optional[str] = None):
    if auto_build and needs_recompile(script_dir): build_module(script_dir)
    import importlib
    return importlib.import_module(MODULE_NAME)
if __name__ == "__main__":
    if "--force" in sys.argv: build_module()
    elif needs_recompile(): build_module()
    else: print(f"[*] {MODULE_NAME} is already up to date. Use --force to rebuild.")
