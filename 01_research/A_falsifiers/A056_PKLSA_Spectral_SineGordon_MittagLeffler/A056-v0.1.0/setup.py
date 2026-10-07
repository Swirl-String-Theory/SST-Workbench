from setuptools import setup, Extension
import os
try:
    import pybind11
    inc=[pybind11.get_include()]
except Exception:
    inc=[]
extra_compile_args=[]; extra_link_args=[]
if os.name=="nt": extra_compile_args=["/O2","/std:c++17","/openmp"]
else: extra_compile_args=["-O3","-std=c++17","-fopenmp"]; extra_link_args=["-fopenmp"]
ext=[]
if inc and os.environ.get("SST_SKIP_NATIVE","0")!="1":
    ext=[Extension("_a056_native",["cpp/native.cpp"],include_dirs=inc,language="c++",extra_compile_args=extra_compile_args,extra_link_args=extra_link_args)]
setup(name="a056-pklsa-sg-ml-falsifier",version="0.1.0",packages=["a056_falsifier"],ext_modules=ext)
