from __future__ import annotations
import argparse, hashlib, importlib.machinery, json, os, platform, subprocess, sys, sysconfig
from pathlib import Path
from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, STAMP_BASENAME

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
CPP = ROOT / CPP_REL
BUILD = ROOT / "build"
STAMP = BUILD / STAMP_BASENAME

def _hash_files(paths):
    h=hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()

def extension_path():
    suffix=sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG/(EXT_BASENAME+suffix)

def _run(cmd,cwd,verbose):
    if verbose: print(LOG_PREFIX,"compile:"," ".join(map(str,cmd)),file=sys.stderr)
    p=subprocess.run(list(map(str,cmd)),cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0: return True
    if verbose:
        print(LOG_PREFIX,"build failed:",p.returncode,file=sys.stderr)
        print("\n".join((p.stdout+"\n"+p.stderr).splitlines()[-80:]),file=sys.stderr)
    return False

def _setuptools_build(out:Path,verbose:bool)->bool:
    try: import pybind11  # noqa
    except Exception: return False
    BUILD.mkdir(exist_ok=True)
    setup_py=BUILD/"_setup_native.py"
    setup_py.write_text('''from setuptools import setup, Extension\nfrom setuptools.command.build_ext import build_ext\nimport pybind11, platform\nclass B(build_ext):\n    def build_extensions(self):\n        is_msvc=self.compiler.compiler_type=="msvc"\n        for e in self.extensions:\n            if is_msvc:\n                e.extra_compile_args=["/O2","/std:c++17","/openmp"]\n            else:\n                e.extra_compile_args=["-O3","-std=c++17","-fopenmp"]\n                e.extra_link_args=["-fopenmp"]\n        super().build_extensions()\nsetup(name="sst_maxwell3_native", package_dir={"":"src"}, packages=["sst_maxwell3_blind"], ext_modules=[Extension("sst_maxwell3_blind._native", [r"'''+str(CPP).replace('\\','\\\\')+'''"], include_dirs=[pybind11.get_include()])], cmdclass={"build_ext":B})\n''',encoding='utf-8')
    return _run([sys.executable,setup_py,"build_ext","--inplace"],ROOT,verbose) and out.exists()

def build_if_needed(force=False,verbose=True):
    out=extension_path(); BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        if verbose: print(LOG_PREFIX,"missing",CPP,file=sys.stderr)
        return out.exists()
    src_hash=_hash_files([CPP])
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get('hash')==src_hash:
                if verbose: print(LOG_PREFIX,"native extension up to date:",out.name,file=sys.stderr)
                return True
        except Exception: pass
    ok=_setuptools_build(out,verbose)
    if ok:
        STAMP.write_text(json.dumps({'hash':src_hash,'python':sys.version,'platform':platform.platform(),'extension':out.name},indent=2),encoding='utf-8')
        if verbose: print(LOG_PREFIX,"built",out.name,file=sys.stderr)
        return True
    if verbose: print(LOG_PREFIX,"native build unavailable; Python fallback remains usable",file=sys.stderr)
    return out.exists()

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--force',action='store_true'); ap.add_argument('--quiet',action='store_true'); ap.add_argument('--strict',action='store_true')
    a=ap.parse_args(argv); ok=build_if_needed(a.force,not a.quiet); return 0 if (ok or not a.strict) else 1
if __name__=='__main__': raise SystemExit(main())
