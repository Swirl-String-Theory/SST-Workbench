"""Build the sst_benchmark_core pybind11 extension."""
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension

ext_modules = [
    Pybind11Extension(
        "sst_benchmark_core",
        ["sst_benchmark_core.cpp"],
    ),
]

setup(
    ext_modules=ext_modules,
)
