from __future__ import annotations
import argparse, hashlib, importlib.machinery, json, os, shutil, subprocess, sys, sysconfig
from pathlib import Path
from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, STAMP_BASENAME

ROOT=Path(__file__).resolve().parents[1]; PKG=Path(__file__).resolve().parent; CPP=ROOT/CPP_REL; BUILD=ROOT/'build'; STAMP=BUILD/STAMP_BASENAME

def extension_path():
    suffix=sysconfig.get_config_var('EXT_SUFFIX') or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG/(EXT_BASENAME+suffix)

def source_hash():
    h=hashlib.sha256(); h.update(CPP.read_bytes()); h.update(Path(__file__).read_bytes()); return h.hexdigest()

def _run(cmd, cwd=ROOT, verbose=True, env=None):
    if verbose: print(LOG_PREFIX,'compile:',' '.join(map(str,cmd)),file=sys.stderr)
    p=subprocess.run(list(map(str,cmd)),cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    if p.returncode!=0 and verbose:
        print(LOG_PREFIX,'build failed:',p.returncode,file=sys.stderr)
        print('\n'.join((p.stdout+'\n'+p.stderr).splitlines()[-80:]),file=sys.stderr)
    return p.returncode==0

def _write_setup(openmp: bool):
    BUILD.mkdir(exist_ok=True)
    setup=BUILD/'_setup_kk_native.py'
    setup.write_text(r'''from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11, os
OPENMP = os.environ.get("KK_OPENMP","1") == "1"
class BuildExt(build_ext):
    def build_extensions(self):
        for ext in self.extensions:
            if self.compiler.compiler_type == 'msvc':
                ext.extra_compile_args=['/O2','/std:c++17'] + (['/openmp'] if OPENMP else [])
                ext.extra_link_args=[]
            else:
                ext.extra_compile_args=['-O3','-std=c++17'] + (['-fopenmp'] if OPENMP else [])
                ext.extra_link_args=(['-fopenmp'] if OPENMP else [])
        super().build_extensions()
setup(name='kk_native_ext', ext_modules=[Extension('kk_native._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()])], cmdclass={'build_ext':BuildExt})
''',encoding='utf-8')
    return setup

def build_if_needed(force=False, verbose=True, strict=False):
    out=extension_path(); BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        if strict: raise FileNotFoundError(CPP)
        return out.exists()
    try: import pybind11  # noqa
    except Exception as e:
        if out.exists() and not force:
            if verbose: print(LOG_PREFIX,'using existing extension; pybind11 build package unavailable',file=sys.stderr)
            return True
        if verbose: print(LOG_PREFIX,'pybind11 unavailable:',e,file=sys.stderr)
        if strict: raise
        return False
    h=source_hash()
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get('hash')==h:
                if verbose: print(LOG_PREFIX,'up to date:',out.name,file=sys.stderr)
                return True
        except Exception: pass
    setup=_write_setup(True)
    for use_openmp in (True,False):
        env=os.environ.copy(); env['KK_OPENMP']='1' if use_openmp else '0'
        if not use_openmp:
            shutil.rmtree(ROOT/'build'/'temp',ignore_errors=True)
        ok=_run([sys.executable,str(setup),'build_ext','--inplace'],verbose=verbose,env=env)
        if ok and out.exists():
            STAMP.write_text(json.dumps({'hash':h,'openmp':use_openmp,'ext':out.name},indent=2),encoding='utf-8')
            if verbose: print(LOG_PREFIX,'built',out.name,'openmp=',use_openmp,file=sys.stderr)
            return True
    if strict: raise RuntimeError('native extension build failed')
    return False

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--force',action='store_true'); ap.add_argument('--quiet',action='store_true'); ap.add_argument('--strict',action='store_true'); a=ap.parse_args()
    try: ok=build_if_needed(a.force,not a.quiet,a.strict)
    except Exception as e:
        print(LOG_PREFIX,e,file=sys.stderr); return 1
    return 0 if ok or not a.strict else 1

if __name__=='__main__': raise SystemExit(main())
