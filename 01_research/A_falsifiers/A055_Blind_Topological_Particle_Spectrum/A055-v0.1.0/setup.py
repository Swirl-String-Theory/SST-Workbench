from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import os
extra = ["/O2","/openmp"] if os.name=="nt" else ["-O3","-fopenmp"]
link = [] if os.name=="nt" else ["-fopenmp"]
ext=[Pybind11Extension("a054_native",["cpp/native.cpp"],cxx_std=17,extra_compile_args=extra,extra_link_args=link)]
setup(name="a054-spectrum-falsifier",version="0.1.0",packages=["a054_spectrum"],
      ext_modules=ext,cmdclass={"build_ext":build_ext})
