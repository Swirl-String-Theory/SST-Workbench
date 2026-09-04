from setuptools import setup, Extension
import sys
import pybind11

if sys.platform == "win32":
    extra_compile_args = ["/O2", "/std:c++17", "/openmp"]
    extra_link_args = []
else:
    extra_compile_args = ["-O3", "-std=c++17", "-fopenmp"]
    extra_link_args = ["-fopenmp"]

ext_modules = [
    Extension(
        "native_ext._native",
        ["native_ext/_native.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    name="sst-material-phase-eft-falsifier",
    version="0.1.1",
    packages=["sst_eft_falsifier", "native_ext"],
    ext_modules=ext_modules,
)
