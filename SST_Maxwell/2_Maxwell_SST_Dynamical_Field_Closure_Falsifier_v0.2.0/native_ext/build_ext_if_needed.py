from __future__ import annotations
import argparse, hashlib, importlib.machinery, json, os, platform, shutil, subprocess, sys, sysconfig
from pathlib import Path
from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, STAMP_BASENAME
ROOT=Path(__file__).resolve().parents[1]; PKG=Path(__file__).resolve().parent; CPP=ROOT/CPP_REL; BUILD=ROOT/'build'; STAMP=BUILD/STAMP_BASENAME

def extension_path():
    suffix=sysconfig.get_config_var('EXT_SUFFIX') or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG/(EXT_BASENAME+suffix)

def src_hash():
    h=hashlib.sha256(); h.update(CPP.read_bytes()); return h.hexdigest()

def _run(cmd,cwd,verbose):
    if verbose: print(LOG_PREFIX,'compile:',' '.join(map(str,cmd)),file=sys.stderr)
    p=subprocess.run(cmd,cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0:return True
    if verbose: print('\n'.join((p.stdout+'\n'+p.stderr).splitlines()[-60:]),file=sys.stderr)
    return False

def _setuptools(out,verbose):
    try: import pybind11
    except Exception: return False
    BUILD.mkdir(exist_ok=True)
    setup=BUILD/'_setup_native.py'
    setup.write_text("from setuptools import setup, Extension\nfrom setuptools.command.build_ext import build_ext\nimport pybind11\nclass B(build_ext):\n def build_extensions(self):\n  for e in self.extensions:\n   e.extra_compile_args=(['/O2','/std:c++17'] if self.compiler.compiler_type=='msvc' else ['-O3','-std=c++17'])\n  super().build_extensions()\nsetup(name='dfc_native',packages=[],ext_modules=[Extension('native_ext._native',['cpp/native.cpp'],include_dirs=[pybind11.get_include()],language='c++')],cmdclass={'build_ext':B})\n",encoding='utf-8')
    return _run([sys.executable,str(setup),'build_ext','--inplace'],ROOT,verbose) and out.exists()

def build_if_needed(force=False,verbose=True):
    out=extension_path(); BUILD.mkdir(exist_ok=True)
    if not CPP.exists(): return False
    h=src_hash()
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get('hash')==h:
                if verbose: print(LOG_PREFIX,'up to date:',out.name,file=sys.stderr)
                return True
        except Exception: pass
    ok=_setuptools(out,verbose)
    if ok:
        STAMP.write_text(json.dumps({'hash':h,'python':sys.version,'platform':platform.platform(),'ext':out.name},indent=2))
        if verbose: print(LOG_PREFIX,'built',out.name,file=sys.stderr)
        return True
    if verbose: print(LOG_PREFIX,'native build unavailable; Python fallback remains usable.',file=sys.stderr)
    return out.exists()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');ap.add_argument('--quiet',action='store_true');ap.add_argument('--strict',action='store_true');a=ap.parse_args()
    ok=build_if_needed(a.force,not a.quiet);return 0 if (ok or not a.strict) else 1
if __name__=='__main__': raise SystemExit(main())
