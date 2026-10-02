from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import numpy as np
import pybind11

is_win = os.name == "nt"
compile_args = ["/O2", "/std:c++17", "/openmp"] if is_win else ["-O3", "-std=c++17", "-fopenmp"]
link_args = [] if is_win else ["-fopenmp"]

ext_modules = [
    Extension(
        "vortex_shear_native",
        ["cpp/vortex_shear_native.cpp"],
        include_dirs=[pybind11.get_include(), np.get_include()],
        language="c++",
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    )
]

setup(
    name="sst-vortex-shear-a049",
    version="0.3.0",
    description="A049 Isotropic Euler-Vortex Dynamic Shear Modulus Blind Falsifier",
    packages=["sst_vortex_shear"],
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
