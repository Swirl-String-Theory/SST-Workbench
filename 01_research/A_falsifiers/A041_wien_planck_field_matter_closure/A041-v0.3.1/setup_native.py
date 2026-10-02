from setuptools import setup, Extension
import numpy as np
import pybind11
ext = Extension(
    "sst_wp.native_ext._native",
    sources=["cpp/native.cpp"],
    include_dirs=[pybind11.get_include(), np.get_include()],
    language="c++",
    extra_compile_args=["/std:c++17"] if __import__('os').name == 'nt' else ["-std=c++17", "-O3"],
)
setup(name="sst_wp_native", version="0.3.1", packages=["sst_wp", "sst_wp.native_ext"], ext_modules=[ext])
