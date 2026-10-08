from setuptools import setup,Extension
import pybind11,sys
extra=['/O2','/std:c++17','/openmp'] if sys.platform.startswith('win') else ['-O3','-std=c++17','-fopenmp']
link=[] if sys.platform.startswith('win') else ['-fopenmp']
setup(name='a054_native',version='0.5.0',ext_modules=[Extension('a054_native',['a054_native.cpp'],include_dirs=[pybind11.get_include(),'.'],language='c++',extra_compile_args=extra,extra_link_args=link)])
