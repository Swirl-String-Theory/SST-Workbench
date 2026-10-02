from setuptools import setup, Extension
import sys
import pybind11
extra_compile_args=['/O2','/std:c++17','/openmp'] if sys.platform=='win32' else ['-O3','-std=c++17','-fopenmp']
extra_link_args=[] if sys.platform=='win32' else ['-fopenmp']
ext=Extension('torsion_native',['cpp/torsion_native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=extra_compile_args,extra_link_args=extra_link_args)
setup(name='sst-torsion-a048',version='0.1.1',packages=['sst_torsion'],ext_modules=[ext])
