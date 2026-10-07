from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib,json,os,platform,shutil,subprocess,sys,sysconfig,importlib.machinery
from .util import canonical_json_sha256,sha256_file,write_json

@dataclass
class BuildResult:
    success: bool
    actual_backend: str
    artifact: str|None
    fingerprint_sha256: str
    compiler: str
    compiler_version: str|None
    flags: list[str]
    error: str|None=None
    def to_dict(self): return asdict(self)


def _cmd_version(exe: str):
    try:
        cp=subprocess.run([exe,"--version"],text=True,capture_output=True,timeout=8)
        s=(cp.stdout or cp.stderr).strip().splitlines(); return s[0] if s else None
    except Exception: return None


def extension_path(package_dir: str|Path,module_name: str) -> Path:
    suffix=sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return Path(package_dir)/(module_name+suffix)


def build_fingerprint(source_paths, *, requested_backend: str, flags: list[str], compiler: str):
    try:
        import pybind11; pybind_ver=pybind11.__version__
    except Exception: pybind_ver=None
    src=[{"path":str(Path(p).resolve()),"sha256":sha256_file(p)} for p in source_paths]
    payload={"sources":src,"requested_backend":requested_backend,"flags":flags,"compiler":compiler,"compiler_version":_cmd_version(compiler),
             "python":sys.version,"cache_tag":getattr(sys.implementation,"cache_tag",None),"ext_suffix":sysconfig.get_config_var("EXT_SUFFIX"),
             "pybind11":pybind_ver,"platform":platform.platform()}
    return canonical_json_sha256(payload),payload


def _write_setup(setup_path: Path, source: Path, package_name: str, module_name: str, package_dir: Path, openmp: bool):
    compile_msvc=['/O2','/std:c++17']+(['/openmp'] if openmp else [])
    compile_other=['-O3','-std=c++17']+(['-fopenmp'] if openmp else [])
    link_other=['-fopenmp'] if openmp else []
    setup_path.write_text(f"""from setuptools import setup, Extension\nfrom setuptools.command.build_ext import build_ext\nimport pybind11\nclass B(build_ext):\n    def build_extensions(self):\n        for e in self.extensions:\n            if self.compiler.compiler_type == "msvc": e.extra_compile_args={compile_msvc!r}\n            else:\n                e.extra_compile_args={compile_other!r}\n                e.extra_link_args={link_other!r}\n        super().build_extensions()\nsetup(name="sst_native_instance", packages=["{package_name}"], package_dir={{"{package_name}":r"{package_dir}"}}, ext_modules=[Extension("{package_name}.{module_name}",[r"{source}"],include_dirs=[pybind11.get_include()])],cmdclass={{"build_ext":B}})\n""",encoding='utf-8')


def build_pybind(instance_root: str|Path, *, source_rel="native/cpp/native.cpp", package_rel="native_ext", module_name="_sst_native", prefer_openmp=True, force=False, verbose=True) -> BuildResult:
    root=Path(instance_root).resolve(); source=root/source_rel; pkg=root/package_rel; pkg.mkdir(parents=True,exist_ok=True); (pkg/"__init__.py").touch()
    build=root/"build"; build.mkdir(exist_ok=True); stamp=build/"PYBIND_BUILD.json"; out=extension_path(pkg,module_name)
    compiler=os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++") or "setuptools-default"
    flags=["C++17","O2/O3"]+(["OpenMP-preferred"] if prefer_openmp else ["serial"])
    fp,payload=build_fingerprint([source],requested_backend="openmp" if prefer_openmp else "serial",flags=flags,compiler=compiler)
    if not force and out.exists() and stamp.exists():
        try:
            prev=json.loads(stamp.read_text(encoding="utf-8"))
            if prev.get("fingerprint_sha256")==fp:
                return BuildResult(True,prev.get("actual_backend","unknown"),str(out),fp,compiler,payload.get("compiler_version"),flags)
        except Exception: pass
    if force or out.exists():
        for old in pkg.glob(module_name+"*"):
            if old.suffix.lower() in {".pyd",".so",".dll"}: old.unlink(missing_ok=True)
    try:
        import pybind11  # noqa
    except Exception as e:
        return BuildResult(False,"none",None,fp,compiler,payload.get("compiler_version"),flags,f"pybind11 unavailable: {e}")
    attempts=[True,False] if prefer_openmp else [False]
    errors=[]
    for use_omp in attempts:
        # IMPORTANT on Windows: use paths relative to the instance root.  Passing the
        # absolute source path makes setuptools mirror the complete drive path below
        # build\temp..., which can exceed Win32/MSVC path limits and produces C1083.
        setup=build/f"_setup_{module_name}.py"
        source_for_setup=Path(source_rel)
        package_for_setup=Path(package_rel)
        _write_setup(setup,source_for_setup,pkg.name,module_name,package_for_setup,use_omp)
        short_temp=build/"_tmp_pybind"
        short_temp.mkdir(parents=True,exist_ok=True)
        cp=subprocess.run([sys.executable,str(setup),"build_ext","--inplace","--build-temp",str(short_temp)],cwd=str(root),text=True,capture_output=True)
        if verbose and cp.returncode!=0: errors.append((cp.stdout+"\n"+cp.stderr)[-5000:])
        if cp.returncode==0 and out.exists():
            actual="openmp" if use_omp else "serial"
            meta={**payload,"fingerprint_sha256":fp,"actual_backend":actual,"artifact":str(out)}; write_json(stamp,meta)
            return BuildResult(True,actual,str(out),fp,compiler,payload.get("compiler_version"),flags)
    return BuildResult(False,"none",None,fp,compiler,payload.get("compiler_version"),flags,"\n---\n".join(errors)[-10000:])
