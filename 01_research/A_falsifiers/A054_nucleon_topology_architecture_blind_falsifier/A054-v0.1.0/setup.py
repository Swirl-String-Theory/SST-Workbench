from setuptools import setup, find_packages
import os, sys
ext=[]
if os.environ.get('A054_BUILD_NATIVE')=='1':
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    args=['/openmp'] if os.name=='nt' else ['-fopenmp']
    link=[] if os.name=='nt' else ['-fopenmp']
    ext=[Pybind11Extension('a054_ntaf._native',['cpp/native.cpp'],cxx_std=17,extra_compile_args=args,extra_link_args=link)]
    cmd={'build_ext':build_ext}
else: cmd={}
setup(name='a054-ntaf',version='0.1.0',package_dir={'':'src'},packages=find_packages('src'),
      install_requires=['numpy>=1.24'],extras_require={'test':['pytest>=8']},ext_modules=ext,cmdclass=cmd,
      entry_points={'console_scripts':['a054-ntaf=a054_ntaf.cli:main']})
