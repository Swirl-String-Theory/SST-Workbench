from setuptools import setup, Extension
import pybind11, sys
extra_compile_args=['/O2','/std:c++17','/openmp','/EHsc','/bigobj'] if sys.platform=='win32' else ['-O3','-std=c++17','-fopenmp']
extra_link_args=[] if sys.platform=='win32' else ['-fopenmp']
ext=Extension('sst_seed_falsifier._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=extra_compile_args,extra_link_args=extra_link_args)
setup(name='sst-trefoil-dynamic-seed-native',version='0.3.0',ext_modules=[ext],package_dir={'':'src'},packages=['sst_seed_falsifier'])
