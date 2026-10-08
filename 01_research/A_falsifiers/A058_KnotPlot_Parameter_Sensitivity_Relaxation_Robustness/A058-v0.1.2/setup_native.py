from setuptools import setup,Extension
import pybind11
setup(name='a058-kpmetrics-native',version='0.1.0',ext_modules=[Extension('kpmetrics_native',['native_ext/kpmetrics.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=['/std:c++17'] if __import__('os').name=='nt' else ['-std=c++17','-O3'])])
