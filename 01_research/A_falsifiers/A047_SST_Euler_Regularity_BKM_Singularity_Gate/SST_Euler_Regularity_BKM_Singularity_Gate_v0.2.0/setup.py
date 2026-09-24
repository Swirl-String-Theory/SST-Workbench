from setuptools import setup, Extension
import pybind11
import sys

extra_compile_args = ["/O2", "/std:c++17"] if sys.platform == "win32" else ["-O3", "-std=c++17"]

ext_modules = [
    Extension(
        "sst_bkm._native",
        ["cpp/native.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=extra_compile_args,
    )
]

setup(
    packages=["sst_bkm"],
    ext_modules=ext_modules,
)
