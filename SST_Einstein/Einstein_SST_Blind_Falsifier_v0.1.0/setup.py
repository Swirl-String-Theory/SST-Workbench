from __future__ import annotations
import os, sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import numpy as np
import pybind11

is_msvc = sys.platform.startswith("win")
want_omp = os.environ.get("SST_OPENMP", "1") not in {"0","false","False"}
if is_msvc:
    compile_args = ["/O2", "/std:c++17"] + (["/openmp"] if want_omp else [])
    link_args = []
else:
    compile_args = ["-O3", "-std=c++17"] + (["-fopenmp"] if want_omp else [])
    link_args = (["-fopenmp"] if want_omp else [])

ext = Extension(
    "sst_einstein._native",
    ["cpp/native.cpp"],
    include_dirs=[pybind11.get_include(), np.get_include()],
    language="c++",
    extra_compile_args=compile_args,
    extra_link_args=link_args,
)
setup(name="sst-einstein-blind-falsifier", version="0.1.0", packages=["sst_einstein", "sst_einstein.gates"], ext_modules=[ext])
