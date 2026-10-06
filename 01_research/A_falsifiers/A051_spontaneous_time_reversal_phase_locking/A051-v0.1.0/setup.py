from setuptools import setup,find_packages,Extension
import sys
ext=[]
try:
    import pybind11
    ext=[Extension('sst_trpl_native',['cpp/trpl_native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=['/std:c++17'] if sys.platform=='win32' else ['-std=c++17'])]
except Exception:
    pass
setup(name='sst-trpl',version='0.1.0',packages=find_packages(include=['sst_trpl','sst_trpl.*']),ext_modules=ext)
