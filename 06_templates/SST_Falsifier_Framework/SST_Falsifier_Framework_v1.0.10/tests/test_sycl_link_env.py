from pathlib import Path
from types import SimpleNamespace
import sst_falsifier.sycl_worker as sw


def test_find_libmmd_near_compiler(monkeypatch,tmp_path):
    monkeypatch.setattr(sw.platform,'system',lambda:'Windows')
    latest=tmp_path/'oneAPI'/'compiler'/'latest'
    cxx=latest/'bin'/'icpx.exe'; cxx.parent.mkdir(parents=True); cxx.write_text('')
    lib=latest/'lib'/'libmmd.lib'; lib.parent.mkdir(parents=True); lib.write_text('x')
    assert sw._find_libmmd(str(cxx))==lib
    env,path=sw._ensure_intel_math_library(str(cxx),{})
    assert path==str(lib)
    assert str(lib.parent) in env['LIB']


def test_merge_semicolon_env_preserves_both_toolchains():
    assert sw._merge_semicolon_env(r'C:\\Intel;C:\\Common',r'C:\\MSVC;C:\\Common') == r'C:\\Intel;C:\\Common;C:\\MSVC'


def test_composite_msvc_oneapi_environment(monkeypatch,tmp_path):
    monkeypatch.setattr(sw.platform,'system',lambda:'Windows')
    msvc_script=tmp_path/'vcvars64.bat'; msvc_script.write_text('')
    oneapi_script=tmp_path/'setvars.bat'; oneapi_script.write_text('')
    msvc_lib=tmp_path/'msvc_lib'; msvc_lib.mkdir(); (msvc_lib/'msvcrt.lib').write_text('x')
    intel_lib=tmp_path/'intel_lib'; intel_lib.mkdir(); (intel_lib/'libmmd.lib').write_text('x')
    monkeypatch.setattr(sw,'_msvc_env_script',lambda:msvc_script)
    monkeypatch.setattr(sw,'_oneapi_env_script',lambda cxx=None:oneapi_script)
    monkeypatch.setattr(sw,'_find_libmmd',lambda cxx=None:intel_lib/'libmmd.lib')

    def fake_run(args,**kwargs):
        target=args[-1]
        body=target
        p=Path(target)
        if p.exists():
            body=p.read_text(encoding='utf-8')
        if 'vcvars64.bat' in body:
            return SimpleNamespace(returncode=0,stdout=f'LIB={msvc_lib}\nPATH=C:\\MSVC\\bin\nINCLUDE=C:\\MSVC\\include\nLIBPATH=C:\\MSVC\\libpath\n',stderr='')
        if 'setvars.bat' in body:
            # Deliberately emulate the regression: Intel emits only its own LIB.
            return SimpleNamespace(returncode=0,stdout=f'LIB={intel_lib}\nPATH=C:\\Intel\\bin\n',stderr='')
        raise AssertionError(args)
    monkeypatch.setattr(sw.subprocess,'run',fake_run)
    env,oneapi,msvc=sw._with_oneapi_environment('icpx.exe',{})
    assert oneapi==str(oneapi_script)
    assert msvc==str(msvc_script)
    assert sw._find_library_in_env(env,'msvcrt.lib')==msvc_lib/'msvcrt.lib'
    assert sw._find_library_in_env(env,'libmmd.lib')==intel_lib/'libmmd.lib'
    assert str(msvc_lib) in env['LIB'] and str(intel_lib) in env['LIB']
    assert r'C:\MSVC\bin' in env['PATH'] and r'C:\Intel\bin' in env['PATH']
