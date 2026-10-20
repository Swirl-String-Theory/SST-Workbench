"""Strict actual-binary C++17 kernel diagnostic, separate from official G5 full-backend authority."""
from __future__ import annotations
import hashlib,math,os,shutil,subprocess,tempfile
from pathlib import Path
from .dynamics import velocities
from .pklsa import load_geometry

def evaluate(root):
    root=Path(root); compiler=os.environ.get('CXX','g++')
    report={'schema':'A065-CPP-KERNEL-QUALIFICATION-1','status':'NOT_RUN_COMPILER_UNAVAILABLE',
            'requested_backend':'cpp-17-binary64','authority':'KERNEL_ONLY_NOT_FRAMEWORK_G5',
            'expected_component_count':1575}
    if not shutil.which(compiler):return report
    src=root/'native'/'filament_velocity.cpp'
    geom=root/'data/D01_EULER/pklsa/trefoil_KnotPlot_relaxed_N300.txt'
    pts=load_geometry(geom)
    report['source_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
    ncomp=0; maximum=0.;sum_sq=0.; max_abs=0.
    with tempfile.TemporaryDirectory(prefix='a065_native_') as d:
        exe=Path(d)/('kernel.exe' if os.name=='nt' else 'kernel')
        cmd=[compiler,'-std=c++17','-O2',str(src),'-o',str(exe)]
        build=subprocess.run(cmd,capture_output=True,text=True,timeout=100)
        if build.returncode:
            report.update(status='FAIL_NATIVE_BUILD',build_stderr=build.stderr[-1200:]);return report
        for nn,stride in ((75,4),(150,2),(300,1)):
            rows=pts[::stride]
            inp=f'{len(rows)} .12 1.0\n'+''.join(' '.join(f'{x:.17g}' for x in row)+'\n' for row in rows)
            cp=subprocess.run([str(exe)],input=inp,capture_output=True,text=True,timeout=100)
            if cp.returncode:
                report.update(status='FAIL_NATIVE_EXECUTION',error=cp.stderr[-1000:]);return report
            actual=[tuple(map(float,line.split())) for line in cp.stdout.strip().splitlines()]
            reference=velocities(rows,0.12,1.0)
            if len(actual)!=len(reference):
                report.update(status='FAIL_SHAPE',observed=len(actual),expected=len(reference));return report
            for a,b in zip(actual,reference):
                for av,bv in zip(a,b):
                    ncomp+=1;err=abs(av-bv);maximum=max(maximum,err/max(abs(bv),1e-13))
                    max_abs=max(max_abs,err);sum_sq+=err*err
    report.update(status='PASS' if maximum<=5e-11 else 'FAIL_NUMERIC_PARITY',
                  comparisons=ncomp,max_relative_component_error=maximum,max_abs_component_error=max_abs,
                  rms_component_error=math.sqrt(sum_sq/ncomp),threshold=5e-11,
                  compiler=compiler,backend_executed='cpp17-serial-fp64',
                  meaning='Velocity-kernel parity only. NOT full RK4, Euler PDE, physical G5 or PKLSA dynamics.')
    return report
