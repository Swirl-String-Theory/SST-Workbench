import os, sys
from setuptools import setup, Extension
ext=[]
if os.environ.get('PKLSA_NO_NATIVE','0') != '1':
    try:
        import pybind11
        if sys.platform=='win32': cargs=['/O2','/std:c++17','/openmp']; largs=[]
        else: cargs=['-O3','-std=c++17','-fopenmp']; largs=['-fopenmp']
        ext=[Extension('pklsa_builder._native',['cpp/pklsa_native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=cargs,extra_link_args=largs)]
    except ImportError:
        # Pure-Python editable install remains possible; run_00_setup.cmd installs pybind11 before production build.
        ext=[]
setup(name='sst-pklsa',version='0.3.0',packages=['sst_pklsa','pklsa_builder'],ext_modules=ext,install_requires=['numpy>=2.0','scipy>=1.13','xlrd>=2.0.1,<3','pybind11>=3.0','setuptools>=70','wheel'],python_requires='>=3.10')
