from setuptools import setup,Extension
import pybind11,sys
extra=['/O2','/EHsc','/bigobj','/openmp'] if sys.platform=='win32' else ['-O3','-std=c++17','-fopenmp']
link=[] if sys.platform=='win32' else ['-fopenmp']
ext=Extension('sst_finite_core_falsifier._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()],language='c++',extra_compile_args=extra,extra_link_args=link)
setup(name='sst-finite-core-native',ext_modules=[ext],package_dir={'':'src'},script_args=['build_ext','--inplace'])
