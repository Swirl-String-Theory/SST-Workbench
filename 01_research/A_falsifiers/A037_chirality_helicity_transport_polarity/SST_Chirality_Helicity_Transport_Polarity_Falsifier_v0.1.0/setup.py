from __future__ import annotations
import os, sys
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

if sys.platform.startswith('win'):
    cxx = ['/O2', '/std:c++17', '/openmp', '/EHsc']
    link = []
else:
    cxx = ['-O3', '-std=c++17', '-fopenmp']
    link = ['-fopenmp']

ext_modules = [
    Pybind11Extension(
        'native_ext._native',
        ['native_ext/_native.cpp'],
        cxx_std=17,
        extra_compile_args=cxx,
        extra_link_args=link,
    )
]

setup(
    name='sst-chirality-helicity-falsifier',
    version='0.1.0',
    packages=['sst_chiral', 'native_ext'],
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},
)
