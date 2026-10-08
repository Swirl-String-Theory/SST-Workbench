from setuptools import setup,Extension
import pybind11,sys
extra=['/O2','/std:c++17','/openmp'] if sys.platform.startswith('win') else ['-O3','-std=c++17','-fopenmp']
link=[] if sys.platform.startswith('win') else ['-fopenmp']
setup(name='mm_native',version='0.1.0',ext_modules=[Extension('mm_native',['mm_native.cpp'],include_dirs=[pybind11.get_include(),'.'],language='c++',extra_compile_args=extra,extra_link_args=link)])
