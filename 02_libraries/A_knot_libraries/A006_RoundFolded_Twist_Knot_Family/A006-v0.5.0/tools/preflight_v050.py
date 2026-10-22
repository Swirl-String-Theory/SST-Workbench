"""Local atomic KnotPlot preflight: create NEW v0.5.0 checkpoint and verify."""
from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parent))
from selection_v050 import locate_executable,check_snapshot,dump
ROOT=Path(__file__).resolve().parents[1]
def main():
    exe=locate_executable(ROOT)
    d=ROOT/'preflight';d.mkdir(exist_ok=True)
    seed=ROOT/'Output/v050/geometry/KNOT_5_2_N1024_ORIG.xyz'
    if not seed.exists():raise FileNotFoundError('Prepare 5_2 N1024 before preflight')
    s=d/'SMOKE_V050.kpc'
    s.write_text('reset all\nmode cb\ncollision fast\nclose = 0.20\nmax-dr = 0.02\nmechforce = on\nelecforce = on\n'+
      f'load {seed.relative_to(ROOT).as_posix()}\ncoords preflight/before.xyz\nago 1\ncoords preflight/after1.xyz\nstop\n')
    with (d/'stdout.log').open('wb') as log:
        done=subprocess.run([str(exe),'-stdin','-nographics'],input=b'read preflight/SMOKE_V050.kpc\n',cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    a=check_snapshot(d/'before.xyz',None,[1024]);b=check_snapshot(d/'after1.xyz',None,[1024])
    if done.returncode or a is False or b is False:
        raise RuntimeError('Atomic headless preflight failed; see preflight/stdout.log')
    dump(d/'PREFLIGHT_PASS.json',{'status':'LOCAL_ATOMIC_ONE_STEP_PASS','exe':str(exe),
       'exe_size':exe.stat().st_size,'exe_mtime_ns':exe.stat().st_mtime_ns,'not_Euler':True})
    print('PASS: KnotPlot ago 1 checkpoint command executed; geometry change must be assessed independently')
if __name__=='__main__':
    try:main()
    except Exception as e:print('PREFLIGHT FAILED',e);sys.exit(4)
