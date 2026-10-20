"""Compile optional C++17 numerical reference and compare all D02 toy response points.
This is a numerical kernel check only, not v1.0.7 framework certification.
"""
from __future__ import annotations
import sys,pathlib,subprocess,tempfile,shutil,os,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from triadic.physics import susceptibility,effective_stiffness,reflection
from triadic.security import readjson,writejson,verify_all

def main():
    verify_all(ROOT)
    compiler=os.getenv('CXX','g++')
    if not shutil.which(compiler):raise SystemExit(f'No compiler {compiler}; native parity UNAVAILABLE, not PASS')
    source=ROOT/'native'/'response.cpp'
    d=readjson(ROOT/'data'/'D02_CLOCK_LINK'/'single_surface.json')
    comp=None
    with tempfile.TemporaryDirectory() as tmp:
        exe=pathlib.Path(tmp)/('response.exe' if os.name=='nt' else 'response')
        build=subprocess.run([compiler,'-std=c++17','-O2',str(source),'-o',str(exe)],capture_output=True,text=True)
        if build.returncode:raise SystemExit('C++ build FAIL: '+build.stderr)
        errors=[];n=0
        for s in d['surfaces'].values():
            if s['kind']=='decoupled':continue
            for xi in d['imaginary_frequencies']:
                for k in [.12,.47,1.2,2.7]:
                    args=[xi,s['M'][0],s['M'][1],s['K'][0][0],s['K'][0][1],s['K'][1][1],s['b'][0],s['b'][1],s['lambda_bare'],k]
                    rr=subprocess.run([str(exe)]+[repr(v) for v in args],capture_output=True,text=True)
                    if rr.returncode:raise SystemExit('Native calc failed '+rr.stderr)
                    obs=[float(x) for x in rr.stdout.split()]
                    lam=effective_stiffness(s,xi)
                    exp=[susceptibility(s,xi),lam,lam/(2*k+lam)]
                    errors.extend([abs(a-b)/max(1e-15,abs(a)) for a,b in zip(obs,exp)]);n+=1
        err=max(errors)
        rep={'status':'NUMERIC_PARITY_PASS' if err<2e-13 else 'NUMERIC_PARITY_FAIL','compiler':compiler,'compiler_version':subprocess.run([compiler,'--version'],capture_output=True,text=True).stdout.splitlines()[0], 'comparisons':n,'maximum_relative_error':err,'threshold':2e-13,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'claim':'OPTIONAL_STDLIB_CPP17_2x2_KERNEL_ONLY'}
        writejson(ROOT/'outputs'/'NATIVE_PARITY.json',rep)
        print(json.dumps(rep,indent=2))
        if rep['status'].endswith('FAIL'):raise SystemExit(1)
if __name__=='__main__':main()
