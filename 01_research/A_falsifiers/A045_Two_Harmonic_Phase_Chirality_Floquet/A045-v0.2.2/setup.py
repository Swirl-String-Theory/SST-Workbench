from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext
import sys

if sys.platform.startswith("win"):
    compile_args = ["/O2", "/openmp"]
    link_args = []
else:
    compile_args = ["-O3", "-fopenmp"]
    link_args = ["-fopenmp"]

ext_modules=[Pybind11Extension(
    "sst_thpcf._native", ["cpp/native.cpp"], cxx_std=17,
    extra_compile_args=compile_args, extra_link_args=link_args,
)]
setup(
    name="sst-thpcf", version="0.2.2",
    packages=find_packages(include=["sst_thpcf","sst_thpcf.*"]),
    ext_modules=ext_modules, cmdclass={"build_ext":build_ext},
)
