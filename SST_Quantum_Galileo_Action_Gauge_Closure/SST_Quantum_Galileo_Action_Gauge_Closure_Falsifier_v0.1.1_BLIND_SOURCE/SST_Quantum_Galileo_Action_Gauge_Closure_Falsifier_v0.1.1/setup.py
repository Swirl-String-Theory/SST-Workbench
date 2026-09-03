from setuptools import setup, Extension, find_packages
import sys

try:
    import pybind11
except ImportError as exc:
    raise SystemExit("pybind11 is required: python -m pip install pybind11") from exc

extra_compile_args = ["/std:c++17", "/O2"] if sys.platform.startswith("win") else ["-std=c++17", "-O3"]
extra_link_args = []

ext_modules = [
    Extension(
        "sst_qgi_native",
        ["cpp/sst_qgi_native.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )
]

setup(
    name="sst-qgi-native",
    version="0.1.1",
    packages=find_packages(include=["sst_qgi", "sst_qgi.*"]),
    ext_modules=ext_modules,
)
