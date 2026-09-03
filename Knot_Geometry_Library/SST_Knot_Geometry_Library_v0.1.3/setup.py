from setuptools import setup, Extension, find_packages
import sys
import pybind11

compile_args=['/std:c++17','/O2','/openmp'] if sys.platform.startswith('win') else ['-std=c++17','-O3','-fopenmp']
link_args=[] if sys.platform.startswith('win') else ['-fopenmp']

ext=Extension(
    'sst_knotlib._sstknot_native',
    ['cpp/native.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++', extra_compile_args=compile_args, extra_link_args=link_args,
)

setup(
    name='sst-knot-geometry', version='0.1.3',
    description='Falsifier-grade knot geometry, frames, bundles and diagnostics for SST',
    packages=find_packages(), ext_modules=[ext],
    python_requires='>=3.10', install_requires=['numpy>=2.0','pybind11>=3.0'],
)
