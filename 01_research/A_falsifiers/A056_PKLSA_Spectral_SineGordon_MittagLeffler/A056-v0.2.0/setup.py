from setuptools import setup, Extension
import os
try:
    import pybind11; inc=[pybind11.get_include()]
except Exception: inc=[]
no_omp=os.environ.get('SST_NO_OPENMP','0')=='1'
if os.name=='nt':
    cargs=['/O2','/std:c++17']+([] if no_omp else ['/openmp']); largs=[]
else:
    cargs=['-O3','-std=c++17']+([] if no_omp else ['-fopenmp']); largs=[] if no_omp else ['-fopenmp']
ext=[]
if inc and os.environ.get('SST_SKIP_NATIVE','0')!='1':
    ext=[Extension('_a056_native',['cpp/native.cpp'],include_dirs=inc,language='c++',extra_compile_args=cargs,extra_link_args=largs)]
setup(name='a056-pklsa-sg-ml-falsifier',version='0.2.0',packages=['a056_falsifier','sst_falsifier_framework'],ext_modules=ext)
