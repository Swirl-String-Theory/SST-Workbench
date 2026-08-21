from __future__ import annotations
import os, sys, shutil
from setuptools import setup, Extension
import pybind11

is_msvc = os.name == "nt"

# setuptools/distutils normally launches vcvarsall.bat in a nested `cmd /c`.
# On some Windows systems a broken CMD AutoRun or a vcvarsall warning leaves a
# non-zero ERRORLEVEL even though the MSVC environment was initialized.  When
# cl.exe is already available, reuse that environment and bypass the nested
# vcvarsall invocation entirely.
if is_msvc and shutil.which("cl.exe"):
    os.environ["DISTUTILS_USE_SDK"] = "1"
    os.environ["MSSdk"] = "1"

compile_args = ["/O2", "/std:c++17", "/EHsc", "/openmp"] if is_msvc else ["-O3", "-std=c++17", "-fopenmp"]
link_args = [] if is_msvc else ["-fopenmp"]

ext = Extension(
    "sst_phase_delay_native",
    sources=["cpp/core.cpp", "cpp/pybind_module.cpp"],
    include_dirs=[pybind11.get_include(), "cpp"],
    language="c++",
    extra_compile_args=compile_args,
    extra_link_args=link_args,
)
setup(name="sst_phase_delay_native", version="0.1.1", ext_modules=[ext])
