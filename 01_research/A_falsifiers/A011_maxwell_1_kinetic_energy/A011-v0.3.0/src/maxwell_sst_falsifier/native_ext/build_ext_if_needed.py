from __future__ import annotations
import argparse, hashlib, importlib.machinery, json, os, platform, shutil, subprocess, sys, sysconfig
from pathlib import Path
from ._config import CPP_REL, EXT_BASENAME, LOG_PREFIX, PACKAGE_DOTTED, STAMP_BASENAME

ROOT=Path(__file__).resolve().parents[3]
PKG=Path(__file__).resolve().parent
CPP=ROOT/CPP_REL
BUILD=ROOT/"build"
STAMP=BUILD/STAMP_BASENAME

def _hash_files(paths):
    h=hashlib.sha256()
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()

def extension_path():
    suffix=sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return PKG/(EXT_BASENAME+suffix)

def have_pybind11():
    try: subprocess.check_output([sys.executable,"-m","pybind11","--includes"],text=True,stderr=subprocess.STDOUT); return True
    except Exception: return False

def _run(cmd,cwd,verbose):
    if verbose: print(f"{LOG_PREFIX} compile: {' '.join(map(str,cmd))}",file=sys.stderr)
    p=subprocess.run(list(map(str,cmd)),cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0: return True
    if verbose:
        print(f"{LOG_PREFIX} build failed: {p.returncode}",file=sys.stderr)
        print("\n".join((p.stdout+"\n"+p.stderr).splitlines()[-60:]),file=sys.stderr)
    return False

def _build_with_setuptools(out,verbose):
    try: import pybind11  # noqa
    except Exception: return False
    BUILD.mkdir(exist_ok=True)
    setup_py=BUILD/f"_setup_{EXT_BASENAME}.py"
    setup_py.write_text(
        "from setuptools import setup, Extension\n"
        "from setuptools.command.build_ext import build_ext\n"
        "import pybind11, os\n"
        "class BuildExt(build_ext):\n"
        "    def build_extensions(self):\n"
        "        for ext in self.extensions:\n"
        "            if self.compiler.compiler_type == 'msvc': ext.extra_compile_args=['/O2','/std:c++17','/EHsc']\n"
        "            else: ext.extra_compile_args=['-O3','-std=c++17']\n"
        "        super().build_extensions()\n"
        f"setup(name='maxwell_sst_native', package_dir={{'':'src'}}, ext_modules=[Extension('{PACKAGE_DOTTED}.{EXT_BASENAME}', [r'{CPP}'], include_dirs=[pybind11.get_include()])], cmdclass={{'build_ext':BuildExt}})\n",
        encoding="utf-8")
    return _run([sys.executable,str(setup_py),"build_ext","--inplace"],ROOT,verbose) and out.exists()

def _direct_build(out,verbose):
    compiler=os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler: return False
    try: includes=subprocess.check_output([sys.executable,"-m","pybind11","--includes"],text=True).split()
    except Exception: return False
    cmd=[compiler,"-O3","-std=c++17","-shared"]
    if platform.system().lower()!="windows": cmd.append("-fPIC")
    cmd += includes+[str(CPP),"-o",str(out)]
    return _run(cmd,ROOT,verbose) and out.exists()

def build_if_needed(force:bool=False,verbose:bool=True):
    out=extension_path(); BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        if verbose: print(f"{LOG_PREFIX} missing source: {CPP}",file=sys.stderr)
        return out.exists()
    if not have_pybind11():
        if verbose: print(f"{LOG_PREFIX} pybind11 unavailable; Python fallback remains usable.",file=sys.stderr)
        return out.exists()
    src_hash=_hash_files([CPP])
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text()).get("hash")==src_hash:
                if verbose: print(f"{LOG_PREFIX} up to date: {out.name}",file=sys.stderr)
                return True
        except Exception: pass
    # Windows: setuptools/MSVC is much more reliable than ad-hoc MinGW Python linking.
    if platform.system().lower()=="windows": ok=_build_with_setuptools(out,verbose) or _direct_build(out,verbose)
    else: ok=_direct_build(out,verbose) or _build_with_setuptools(out,verbose)
    if ok:
        STAMP.write_text(json.dumps({"hash":src_hash,"python":sys.version,"platform":platform.platform(),"ext":out.name},indent=2))
        if verbose: print(f"{LOG_PREFIX} built {out.name}",file=sys.stderr)
    elif verbose: print(f"{LOG_PREFIX} native build unavailable; Python fallback remains usable.",file=sys.stderr)
    return bool(ok)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--force",action="store_true"); ap.add_argument("--quiet",action="store_true"); ap.add_argument("--strict",action="store_true")
    a=ap.parse_args(); ok=build_if_needed(a.force,not a.quiet); return 0 if (ok or not a.strict) else 1
if __name__=="__main__": raise SystemExit(main())
