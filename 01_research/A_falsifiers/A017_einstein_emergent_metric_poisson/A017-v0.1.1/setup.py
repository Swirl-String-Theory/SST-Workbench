from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os, pybind11

class SSTBuildExt(build_ext):
    def build_extensions(self):
        ct = getattr(self.compiler, "compiler_type", "")
        disable_omp = os.environ.get("SST_DISABLE_OPENMP", "0") == "1"
        for ext in self.extensions:
            if ct == "msvc":
                ext.extra_compile_args = ["/O2", "/std:c++17"] + ([] if disable_omp else ["/openmp"])
                ext.extra_link_args = []
            else:
                ext.extra_compile_args = ["-O3", "-std=c++17"] + ([] if disable_omp else ["-fopenmp"])
                ext.extra_link_args = [] if disable_omp else ["-fopenmp"]
                if os.name == "nt":
                    # Reduce MinGW runtime-DLL surprises where supported.
                    ext.extra_link_args += ["-static-libgcc", "-static-libstdc++"]
        super().build_extensions()

ext_modules = [Extension(
    "einstein_sst_gates._fast",
    ["cpp/einstein_sst_fast.cpp"],
    include_dirs=[pybind11.get_include()],
    language="c++",
)]

setup(
    packages=find_packages("src"),
    package_dir={"": "src"},
    ext_modules=ext_modules,
    cmdclass={"build_ext": SSTBuildExt},
    zip_safe=False,
)
