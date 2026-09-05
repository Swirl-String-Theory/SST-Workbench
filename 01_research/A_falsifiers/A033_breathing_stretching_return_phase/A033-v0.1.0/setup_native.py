from setuptools import setup, Extension
import pybind11, sys

extra_compile_args=[]
extra_link_args=[]
if sys.platform.startswith('win'):
    extra_compile_args=['/O2','/std:c++17','/openmp']
else:
    extra_compile_args=['-O3','-std=c++17','-fopenmp']
    extra_link_args=['-fopenmp']

ext=Extension(
    'sst_bsrp_falsifier._native',
    ['cpp/native.cpp'],
    include_dirs=[pybind11.get_include()],
    language='c++',
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)
setup(name='sst-bsrp-native', version='0.1.1', package_dir={'':'src'}, ext_modules=[ext])
