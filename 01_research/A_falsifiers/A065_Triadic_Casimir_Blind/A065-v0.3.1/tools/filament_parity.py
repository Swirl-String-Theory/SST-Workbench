"""C++17 strict binary64 parity for the new dynamic filament velocity kernel.
Does not certify 3-D Euler, PKLSA physics or framework gate G5.
"""
from __future__ import annotations
import os,sys,json,subprocess,shutil,hashlib,tempfile,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from triadic.dynamics import velocities
from triadic.pklsa import load_geometry
from triadic.security import readjson,writejson,verify_all

def main():
    verify_all(R)
    compiler=os.getenv('CXX','g++')
    if not shutil.which(compiler):
        print('C++17 filament parity NOT_RUN_COMPILER_UNAVAILABLE');return 4
    src=R/'native'/'filament_velocity.cpp';points=load_geometry(R/'data'/'D01_EULER'/'pklsa'/'trefoil_KnotPlot_relaxed_N300.txt')[::4]
    eps=0.12;gamma=1.0
    inp=f'{len(points)} {eps:.17g} {gamma:.17g}\n'+''.join(' '.join(f'{v:.17g}' for v in p)+'\n' for p in points)
    with tempfile.TemporaryDirectory() as d:
        exe=Path(d)/('filament.exe' if os.name=='nt' else 'filament')
        cmd=[compiler,'-std=c++17','-O2',str(src),'-o',str(exe)]
        cp=subprocess.run(cmd,text=True,capture_output=True)
        if cp.returncode: raise RuntimeError('C++17 build failed: '+cp.stderr[-2000:])
        run=subprocess.run([str(exe)],input=inp,text=True,capture_output=True)
        if run.returncode:raise RuntimeError('C++17 runtime failed: '+run.stderr)
        native=[tuple(float(x) for x in line.split()) for line in run.stdout.splitlines()]
    python=velocities(points,eps,gamma)
    if len(native)!=len(python):raise AssertionError('native wrong shape')
    maximum=max(abs(a-b)/max(1e-13,abs(b)) for row,ref in zip(native,python) for a,b in zip(row,ref))
    rep={'schema':'A065-FILAMENT-CPP-PARITY-1','status':'PASS' if maximum<=5e-11 else 'FAIL',
         'comparisons':len(points)*3,'max_relative_component_error':maximum,'threshold':5e-11,
         'compiler':compiler,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
         'evidence':'numeric_parity_only','official_framework_G5':'NOT_CLOSED'}
    writejson(R/'outputs'/'FILAMENT_CPP_PARITY.json',rep)
    print(json.dumps(rep,indent=2));return 0 if rep['status']=='PASS' else 2
if __name__=='__main__':raise SystemExit(main())
