#!/usr/bin/env python3
"""One atomic KnotPlot headless checkpoint to qualify -stdin on this particular PC."""
import sys,subprocess,os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from run_campaign import preflight_exe,validate_snapshot
from build_v040 import write_json

def main():
    try:exe=preflight_exe()
    except Exception as exc:print('PREFLIGHT BLOCKED',exc);return 3
    folder=ROOT/'preflight';folder.mkdir(exist_ok=True)
    script=folder/'SMOKE_KNOTPLOT_STDIN.kpc'
    script.write_text('reset all\nmode cb\ncollision fast\nclose = 0.20\nmax-dr = 0.02\nmechforce = on\nelecforce = on\n'
        'load output/seeds/5_2_N1024.kpt\ncoords preflight/before.xyz\nago 1\ncoords preflight/after1.xyz\necho END_PREFLIGHT\nstop\n')
    try:
      run=subprocess.run([str(exe),'-stdin','-nographics'],input=b'read preflight/SMOKE_KNOTPLOT_STDIN.kpc\n',
         cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180,check=False)
    except Exception as exc:print('PREFLIGHT FAIL',exc);return 4
    (folder/'preflight_stdout.log').write_bytes(run.stdout)
    a=validate_snapshot(folder/'before.xyz',1024);b=validate_snapshot(folder/'after1.xyz',1024)
    if run.returncode!=0 or a is None or b is None or (a==b).all():
      print('PREFLIGHT FAIL: returncode=',run.returncode,'; before/after valid=',a is not None,b is not None,
          'changed=',a is not None and b is not None and not (a==b).all());return 5
    write_json(folder/'PREFLIGHT_PASS.json',{'status':'LOCAL_ATOMIC_ONE_STEP_PASS','exe':str(exe),'exe_size':exe.stat().st_size,'exe_mtime_ns':exe.stat().st_mtime_ns,'headless_stdin':True,'physical_Euler':'NOT_TESTED'})
    print('PREFLIGHT PASS: KnotPlot -stdin -nographics + ago 1 + coords works on this PC')
    return 0
if __name__=='__main__':raise SystemExit(main())
