from __future__ import annotations
import argparse,hashlib,importlib.machinery,json,os,platform,shutil,subprocess,sys,sysconfig
from pathlib import Path
from ._config import CPP_REL,EXT_BASENAME,LOG_PREFIX,STAMP_BASENAME
ROOT=Path(__file__).resolve().parents[1]; PKG=Path(__file__).resolve().parent; CPP=ROOT/CPP_REL; BUILD=ROOT/"build"; STAMP=BUILD/STAMP_BASENAME

def _hash_files(paths):
    h=hashlib.sha256()
    for p in paths: h.update(str(p.relative_to(ROOT)).encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return h.hexdigest()
def extension_path():
    suffix=sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]; return PKG/(EXT_BASENAME+suffix)
def have_pybind11():
    try: import pybind11; return True
    except Exception: return False
def _run(cmd,cwd,verbose):
    if verbose: print(f"{LOG_PREFIX} compile: {' '.join(map(str,cmd))}",file=sys.stderr)
    p=subprocess.run(list(map(str,cmd)),cwd=str(cwd),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if p.returncode==0:return True
    if verbose:
        print(f"{LOG_PREFIX} build failed: {p.returncode}",file=sys.stderr); print("\n".join((p.stdout+"\n"+p.stderr).splitlines()[-60:]),file=sys.stderr)
    return False

def _build_setuptools(out,verbose):
    try: import pybind11
    except Exception:return False
    BUILD.mkdir(exist_ok=True); setup_py=BUILD/f"_setup_{EXT_BASENAME}.py"
    setup_py.write_text(
      "from setuptools import setup, Extension\nfrom setuptools.command.build_ext import build_ext\nimport pybind11\n"
      "class BuildExt(build_ext):\n"
      "  def build_extensions(self):\n"
      "    for ext in self.extensions:\n"
      "      if self.compiler.compiler_type == 'msvc': ext.extra_compile_args=['/O2','/std:c++17','/EHsc']\n"
      "      else: ext.extra_compile_args=['-O3','-std=c++17']\n"
      "    super().build_extensions()\n"
      f"setup(name='maxwell5_native_ext',ext_modules=[Extension('maxwell5_native.{EXT_BASENAME}',['{CPP_REL.as_posix()}'],include_dirs=[pybind11.get_include()],language='c++')],cmdclass={{'build_ext':BuildExt}})\n",
      encoding="utf-8")
    return _run([sys.executable,str(setup_py),"build_ext","--inplace"],ROOT,verbose) and out.exists()

def _build_direct(out,verbose):
    compiler=os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not compiler:return False
    if Path(str(compiler)).name.lower() in ("cl","cl.exe"): return False
    try: includes=subprocess.check_output([sys.executable,"-m","pybind11","--includes"],text=True).split()
    except Exception:return False
    cmd=[compiler,"-O3","-std=c++17","-shared"]
    if platform.system().lower()!="windows": cmd.append("-fPIC")
    cmd += [*includes,str(CPP),"-o",str(out)]
    # On Windows, direct GNU builds need the Python import library; setuptools fallback is preferred if this fails.
    if platform.system().lower()=="windows":
        maj,minor=sys.version_info[:2]
        for d in [Path(sys.base_prefix)/"libs",Path(sys.prefix)/"libs"]:
            if d.exists(): cmd.append("-L"+str(d))
        cmd.append(f"-lpython{maj}{minor}")
    return _run(cmd,ROOT,verbose) and out.exists()

def build_if_needed(force=False,verbose=True):
    out=extension_path(); BUILD.mkdir(exist_ok=True)
    if not CPP.exists():
        if verbose: print(f"{LOG_PREFIX} missing source: {CPP}",file=sys.stderr)
        return out.exists()
    if not have_pybind11():
        if verbose: print(f"{LOG_PREFIX} pybind11 missing; install requirements first.",file=sys.stderr)
        return out.exists()
    src_hash=_hash_files([CPP]); meta={"hash":src_hash,"ext":out.name,"cpp":str(CPP_REL),"python":sys.version}
    if not force and out.exists() and STAMP.exists():
        try:
            if json.loads(STAMP.read_text(encoding="utf-8")).get("hash")==src_hash:
                if verbose: print(f"{LOG_PREFIX} up to date: {out.name}",file=sys.stderr)
                return True
        except Exception: pass
    ok=_build_direct(out,verbose)
    if not ok: ok=_build_setuptools(out,verbose)
    if ok and out.exists():
        STAMP.write_text(json.dumps(meta,indent=2),encoding="utf-8")
        if verbose: print(f"{LOG_PREFIX} built {out.name}",file=sys.stderr)
        return True
    if verbose: print(f"{LOG_PREFIX} C++ build failed; inspect compiler output above.",file=sys.stderr)
    return out.exists()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--force",action="store_true"); ap.add_argument("--quiet",action="store_true"); ap.add_argument("--strict",action="store_true"); args=ap.parse_args(); ok=build_if_needed(args.force,not args.quiet); return 0 if (ok or not args.strict) else 1
if __name__=="__main__": raise SystemExit(main())
