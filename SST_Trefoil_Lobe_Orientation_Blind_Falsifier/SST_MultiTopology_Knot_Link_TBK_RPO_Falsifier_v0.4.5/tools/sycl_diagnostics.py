from __future__ import annotations
import os, sys, sysconfig, subprocess, shutil, pathlib, json
ROOT=pathlib.Path(__file__).resolve().parents[1]
CPP=ROOT/'cpp'
OUT=ROOT/'build'/'sycl_diagnostics'
OUT.mkdir(parents=True,exist_ok=True)

def icpx():
    return shutil.which('icpx') or shutil.which('icpx.exe') or str(pathlib.Path(os.environ.get('ONEAPI_ROOT',r'C:\Program Files (x86)\Intel\oneAPI'))/'compiler'/'latest'/'bin'/'icpx.exe')

def suffix(): return sysconfig.get_config_var('EXT_SUFFIX') or '.pyd'

def includes():
    import pybind11
    return ['-I'+sysconfig.get_paths()['include'],'-I'+pybind11.get_include()]

def pylib():
    root=pathlib.Path(sys.base_prefix)
    return str(root/'libs'/f'python{sys.version_info.major}{sys.version_info.minor}.lib')

def compile_probe(i,name):
    src=CPP/name
    out=ROOT/(f'_sst_sycl_probe{i}'+suffix())
    try: out.unlink()
    except FileNotFoundError: pass
    cmd=[icpx(),'-fsycl','-fsycl-device-code-split=per_kernel','-O2','-std=c++17',*includes(),str(src),'-shared','-o',str(out),pylib()]
    print('\n[compile]', ' '.join(cmd))
    cp=subprocess.run(cmd,cwd=ROOT)
    return out,cp.returncode

def run_child(i,expr):
    code=("import os; "
          "from native_ext.dll_search import configure_windows_dll_search; configure_windows_dll_search(verbose=True); "
          f"import _sst_sycl_probe{i} as p; print('IMPORT_OK'); print({expr})")
    env=os.environ.copy(); env.setdefault('SYCL_CACHE_PERSISTENT','0')
    cp=subprocess.run([sys.executable,'-X','faulthandler','-c',code],cwd=ROOT,env=env,text=True)
    return cp.returncode

def main():
    probes=[
      (0,'sycl_probe_0_bind.cpp','p.hello()'),
      (1,'sycl_probe_1_device.cpp','p.device()'),
      (2,'sycl_probe_2_float_kernel.cpp','p.run()'),
      (3,'sycl_probe_3_double_kernel.cpp','p.capability()'),
    ]
    res={}
    print('SYCL_CACHE_PERSISTENT=',os.environ.get('SYCL_CACHE_PERSISTENT','<unset>'))
    for i,src,expr in probes:
        out,crc=compile_probe(i,src)
        r={'compile_rc':crc,'path':str(out)}
        if crc==0: r['import_run_rc']=run_child(i,expr)
        res[f'probe_{i}']=r
        print('[result]',i,r)
    path=OUT/'diagnostics.json'; path.write_text(json.dumps(res,indent=2))
    print('\nWROTE',path)
    # probe0/1/2 must succeed. Probe3 only checks fp64 capability and should import.
    return 0 if all(v.get('compile_rc')==0 and v.get('import_run_rc')==0 for v in res.values()) else 2
if __name__=='__main__': raise SystemExit(main())
