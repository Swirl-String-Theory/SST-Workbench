#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent


def timed(force_python: bool, n: int):
    env=os.environ.copy(); env['PYTHONPATH']=str(ROOT)+os.pathsep+env.get('PYTHONPATH',''); env['SST_HOPF_FORCE_PYTHON']='1' if force_python else '0'
    out=ROOT/'results'/('bench_python' if force_python else 'bench_cpp')
    cmd=[sys.executable,'02_analytische_hopf_benchmark.py','--output',str(out),'--resolutions',str(max(16,n//2)),str(n),'--integer-tolerance','0.30']
    t=time.perf_counter(); p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True); dt=time.perf_counter()-t
    return {'backend':'python' if force_python else 'cpp','n':n,'seconds':dt,'returncode':p.returncode,'stdout_tail':'\n'.join(p.stdout.splitlines()[-8:])}


def main():
    n=int(sys.argv[1]) if len(sys.argv)>1 else 48
    cpp=timed(False,n); py=timed(True,n)
    speedup=py['seconds']/cpp['seconds'] if cpp['seconds']>0 else None
    result={'cpp':cpp,'python':py,'speedup_python_over_cpp':speedup,'ok':cpp['returncode']==0 and py['returncode']==0}
    out=ROOT/'results'/'cpp_vs_python_benchmark.json'; out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2)); return 0 if result['ok'] else 2

if __name__=='__main__': raise SystemExit(main())
