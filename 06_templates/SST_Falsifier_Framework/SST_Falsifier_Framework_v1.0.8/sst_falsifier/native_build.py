from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import importlib.machinery,json,os,platform,re,shutil,subprocess,sys,sysconfig
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
    compiler_family: str|None=None
    toolset: str|None=None
    python_abi: str|None=None
    def to_dict(self): return asdict(self)


def _compiler_family(exe: str|None) -> str|None:
    if not exe: return None
    n=re.split(r"[\\/]",str(exe))[-1].lower()
    if n in {"cl","cl.exe"}: return "msvc"
    if "clang" in n: return "clang"
    if n in {"gcc","gcc.exe","g++","g++.exe","c++","c++.exe"}: return "gcc-compatible"
    return "unknown"


def _toolset_from_path(exe: str|None) -> str|None:
    if not exe: return None
    m=re.search(r"[\\/]MSVC[\\/]([^\\/]+)[\\/]",str(exe),re.I)
    return m.group(1) if m else None


def _python_abi() -> str:
    tag=getattr(sys.implementation,"cache_tag","") or "python"
    if tag.startswith("cpython-"): tag="cp"+tag.split("-",1)[1]
    plat=(sysconfig.get_platform() or platform.system()).replace("-","_")
    return f"{tag}-{plat}"


def _cmd_version(exe: str|None):
    if not exe or exe in {"setuptools-default","unknown"}: return None
    try:
        family=_compiler_family(exe)
        args=[exe] if family=="msvc" else [exe,"--version"]
        cp=subprocess.run(args,text=True,capture_output=True,timeout=8)
        lines=(cp.stdout+"\n"+cp.stderr).strip().splitlines()
        if family=="msvc":
            for line in lines:
                if "compiler version" in line.lower(): return line.strip()
        return lines[0].strip() if lines else None
    except Exception: return None


def _compiler_from_build_log(text: str) -> str|None:
    """Extract the compiler executable actually invoked by setuptools.

    This deliberately does not trust CXX/PATH on Windows: CPython/setuptools may
    select MSVC even when a Strawberry/MinGW c++.exe appears earlier on PATH.
    """
    patterns=[
        r'^\s*"([^"]*\\cl\.exe)"\s+',
        r'^\s*"([^"]*\\clang\+\+\.exe)"\s+',
        r'^\s*"([^"]*\\g\+\+\.exe)"\s+',
        r'^\s*"([^"]*\\c\+\+\.exe)"\s+',
        r'^\s*([^\s"]*(?:cl|clang\+\+|g\+\+|c\+)\.exe)\s+',
        r'^\s*([^\s]+(?:clang\+\+|g\+\+|c\+\+|gcc))\s+',
    ]
    for line in text.splitlines():
        for pat in patterns:
            m=re.search(pat,line,re.I)
            if m:
                token=m.group(1)
                p=Path(token)
                if p.exists(): return str(p.resolve())
                q=shutil.which(token)
                return q or token
    return None


def _setuptools_compiler_hint() -> str:
    if platform.system().lower()=="windows":
        # Ask setuptools' own MSVC environment first. This matches the compiler
        # used for official Windows CPython extension modules.
        try:
            from setuptools._distutils._msvccompiler import _get_vc_env
            env=_get_vc_env("x64")
            for d in env.get("path","").split(os.pathsep):
                p=Path(d)/"cl.exe"
                if p.exists(): return str(p.resolve())
        except Exception:
            pass
        q=shutil.which("cl.exe")
        if q: return q
    return os.environ.get("CXX") or shutil.which("c++") or shutil.which("g++") or shutil.which("clang++") or "setuptools-default"


def extension_path(package_dir: str|Path,module_name: str) -> Path:
    suffix=sysconfig.get_config_var("EXT_SUFFIX") or importlib.machinery.EXTENSION_SUFFIXES[0]
    return Path(package_dir)/(module_name+suffix)


def build_fingerprint(source_paths, *, requested_backend: str, flags: list[str], compiler: str, compiler_version: str|None=None, build_policy: str|None=None):
    try:
        import pybind11; pybind_ver=pybind11.__version__
    except Exception: pybind_ver=None
    cv=compiler_version if compiler_version is not None else _cmd_version(compiler)
    src=[{"path":str(Path(p).resolve()),"sha256":sha256_file(p)} for p in source_paths]
    payload={
        "sources":src,
        "requested_backend":requested_backend,
        "build_policy":build_policy,
        "flags":flags,
        "compiler":compiler,
        "compiler_family":_compiler_family(compiler),
        "compiler_version":cv,
        "toolset":_toolset_from_path(compiler),
        "python":sys.version,
        "python_abi":_python_abi(),
        "cache_tag":getattr(sys.implementation,"cache_tag",None),
        "ext_suffix":sysconfig.get_config_var("EXT_SUFFIX"),
        "pybind11":pybind_ver,
        "platform":platform.platform(),
    }
    return canonical_json_sha256(payload),payload


def _write_setup(setup_path: Path, source: Path, package_name: str, module_name: str, package_dir: Path, openmp: bool):
    compile_msvc=['/O2','/std:c++17']+(['/openmp'] if openmp else [])
    compile_other=['-O3','-std=c++17']+(['-fopenmp'] if openmp else [])
    link_other=['-fopenmp'] if openmp else []
    setup_path.write_text(f"""from setuptools import setup, Extension\nfrom setuptools.command.build_ext import build_ext\nimport pybind11\nclass B(build_ext):\n    def build_extensions(self):\n        for e in self.extensions:\n            if self.compiler.compiler_type == \"msvc\": e.extra_compile_args={compile_msvc!r}\n            else:\n                e.extra_compile_args={compile_other!r}\n                e.extra_link_args={link_other!r}\n        super().build_extensions()\nsetup(name=\"sst_native_instance\", packages=[\"{package_name}\"], package_dir={{\"{package_name}\":r\"{package_dir}\"}}, ext_modules=[Extension(\"{package_name}.{module_name}\",[r\"{source}\"],include_dirs=[pybind11.get_include()])],cmdclass={{\"build_ext\":B}})\n""",encoding='utf-8')


def _result_from_payload(success,actual,artifact,fp,payload,flags,error=None):
    return BuildResult(
        success,actual,artifact,fp,payload.get("compiler","unknown"),payload.get("compiler_version"),flags,error,
        payload.get("compiler_family"),payload.get("toolset"),payload.get("python_abi")
    )


def build_pybind(instance_root: str|Path, *, source_rel="native/cpp/native.cpp", package_rel="native_ext", module_name="_sst_native", prefer_openmp=True, force=False, verbose=True) -> BuildResult:
    root=Path(instance_root).resolve(); source=root/source_rel; pkg=root/package_rel; pkg.mkdir(parents=True,exist_ok=True); (pkg/"__init__.py").touch()
    build=root/"build"; build.mkdir(exist_ok=True); stamp=build/"PYBIND_BUILD.json"; out=extension_path(pkg,module_name)
    policy="openmp-preferred" if prefer_openmp else "serial"

    # Cache validation uses the compiler recorded from the *actual previous build*.
    if not force and out.exists() and stamp.exists():
        try:
            prev=json.loads(stamp.read_text(encoding="utf-8"))
            prev_compiler=prev.get("compiler") or "setuptools-default"
            prev_actual=prev.get("actual_backend","unknown")
            prev_flags=["C++17","O2/O3",("OpenMP" if prev_actual=="openmp" else "serial")]
            fp,payload=build_fingerprint([source],requested_backend=prev_actual,flags=prev_flags,compiler=prev_compiler,build_policy=policy)
            if prev.get("fingerprint_sha256")==fp:
                return _result_from_payload(True,prev_actual,str(out),fp,payload,prev_flags)
        except Exception: pass

    if force or out.exists():
        for old in pkg.glob(module_name+"*"):
            if old.suffix.lower() in {".pyd",".so",".dll"}: old.unlink(missing_ok=True)
    try:
        import pybind11  # noqa
    except Exception as e:
        hint=_setuptools_compiler_hint(); flags=["C++17","O2/O3",policy]
        fp,payload=build_fingerprint([source],requested_backend=policy,flags=flags,compiler=hint,build_policy=policy)
        return _result_from_payload(False,"none",None,fp,payload,flags,f"pybind11 unavailable: {e}")

    attempts=[True,False] if prefer_openmp else [False]
    errors=[]
    for use_omp in attempts:
        setup=build/f"_setup_{module_name}.py"
        # Keep source/object paths short on Windows. Absolute source paths make
        # setuptools mirror the full drive path below build\\temp and can trigger C1083.
        _write_setup(setup,Path(source_rel),pkg.name,module_name,Path(package_rel),use_omp)
        short_temp=build/"_tmp_pybind"; short_temp.mkdir(parents=True,exist_ok=True)
        cp=subprocess.run([sys.executable,str(setup),"build_ext","--inplace","--build-temp",str(short_temp)],cwd=str(root),text=True,capture_output=True)
        log=(cp.stdout or "")+"\n"+(cp.stderr or "")
        if verbose and cp.returncode!=0: errors.append(log[-5000:])
        if cp.returncode==0 and out.exists():
            actual="openmp" if use_omp else "serial"
            actual_compiler=_compiler_from_build_log(log) or _setuptools_compiler_hint()
            actual_flags=["C++17","O2/O3",("OpenMP" if use_omp else "serial")]
            fp,payload=build_fingerprint([source],requested_backend=actual,flags=actual_flags,compiler=actual_compiler,build_policy=policy)
            meta={**payload,"fingerprint_sha256":fp,"actual_backend":actual,"artifact":str(out),"build_log_compiler_detected":bool(_compiler_from_build_log(log))}
            write_json(stamp,meta)
            return _result_from_payload(True,actual,str(out),fp,payload,actual_flags)

    hint=_setuptools_compiler_hint(); flags=["C++17","O2/O3",policy]
    fp,payload=build_fingerprint([source],requested_backend=policy,flags=flags,compiler=hint,build_policy=policy)
    return _result_from_payload(False,"none",None,fp,payload,flags,"\n---\n".join(errors)[-10000:])
