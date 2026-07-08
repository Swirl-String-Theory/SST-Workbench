from __future__ import annotations

from pathlib import Path
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class BuildExt(build_ext):
    c_opts = {
        "msvc": ["/O2", "/std:c++17", "/DBUILD_PYBIND11_MODULE"],
        "unix": ["-O3", "-std=c++17", "-DBUILD_PYBIND11_MODULE"],
    }

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        for ext in self.extensions:
            ext.extra_compile_args = opts
        super().build_extensions()


def get_pybind_include() -> str:
    import pybind11
    return pybind11.get_include()


root = Path(__file__).parent

setup(
    name="sst-torsion-impedance",
    version="0.8.19.0",
    description="Standalone SST research-track Core--Torsion impedance audit module",
    py_modules=[],
    ext_modules=[
        Extension(
            "sst_torsion_impedance",
            [str(root / "src" / "sst_torsion_impedance.cpp")],
            include_dirs=[get_pybind_include()],
            language="c++",
        )
    ],
    cmdclass={"build_ext": BuildExt},
    python_requires=">=3.9",
)
