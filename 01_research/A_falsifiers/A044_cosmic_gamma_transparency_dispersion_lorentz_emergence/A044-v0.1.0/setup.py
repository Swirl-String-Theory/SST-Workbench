from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "sst_cgtdlef._native",
        ["cpp/bindings.cpp"],
        cxx_std=17,
    )
]

setup(
    name="sst-cgtdlef",
    version="0.1.0",
    description="Blind cosmic gamma transparency / dispersion qualification falsifier",
    packages=["sst_cgtdlef"],
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    python_requires=">=3.10",
)
