from setuptools import setup, Extension
import pybind11,sys
if sys.platform.startswith('win'):
    cargs=['/std:c++17','/O2','/EHsc','/bigobj','/openmp'];largs=[]
else:
    cargs=['-std=c++17','-O3','-fopenmp'];largs=['-fopenmp']
ext=Extension('sst_threaded_hole_falsifier._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=cargs,extra_link_args=largs)
setup(name='sst-threaded-hole-falsifier-native',version='0.3.0',package_dir={'':'src'},packages=['sst_threaded_hole_falsifier'],ext_modules=[ext])
