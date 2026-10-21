from setuptools import setup, Extension, find_packages
try:
    import pybind11
    ext=[Extension("sst_cgtdlef._native",["cpp/bindings.cpp"],include_dirs=[pybind11.get_include()],language="c++",extra_compile_args=["/std:c++17"] if __import__('os').name=='nt' else ["-std=c++17"])]
except Exception:
    ext=[]
setup(name="sst-cgtdlef",version="0.2.0",packages=find_packages(),ext_modules=ext)
