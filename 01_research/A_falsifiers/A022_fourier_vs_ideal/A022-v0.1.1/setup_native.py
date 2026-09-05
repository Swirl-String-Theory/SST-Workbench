import os
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

is_win = os.name == "nt"
ext_modules = [
    Pybind11Extension(
        "sst_fourier_ideal_falsifier._native",
        ["cpp/native.cpp"],
        cxx_std=17,
        extra_compile_args=["/O2", "/openmp"] if is_win else ["-O3", "-fopenmp"],
        extra_link_args=[] if is_win else ["-fopenmp"],
    )
]
setup(
    name="sst-fourier-ideal-native",
    package_dir={"": "src"},
    packages=["sst_fourier_ideal_falsifier"],
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
