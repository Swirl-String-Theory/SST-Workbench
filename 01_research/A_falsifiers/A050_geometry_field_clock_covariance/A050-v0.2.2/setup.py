from setuptools import setup, Extension
try:
    import pybind11
    include_dirs = [pybind11.get_include()]
except Exception:
    include_dirs = []

ext_modules = []
if include_dirs:
    ext_modules.append(
        Extension(
            "sst_gfcc_blind.native_ext._native",
            ["cpp/native.cpp"],
            include_dirs=include_dirs,
            language="c++",
            extra_compile_args=["/std:c++17"] if __import__('sys').platform.startswith('win') else ["-std=c++17", "-O3"],
        )
    )
setup(ext_modules=ext_modules)
