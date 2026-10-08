from setuptools import setup, Extension
import pybind11, sys
extra=['/O2','/openmp'] if sys.platform=='win32' else ['-O3','-fopenmp']
link=[] if sys.platform=='win32' else ['-fopenmp']
setup(name='a054-mechanism-injection',version='0.4.0.post3',packages=['experiment'],ext_modules=[Extension('experiment._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=extra,extra_link_args=link)])
