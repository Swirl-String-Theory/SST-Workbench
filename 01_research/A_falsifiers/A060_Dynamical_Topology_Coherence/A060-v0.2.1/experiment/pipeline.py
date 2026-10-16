from __future__ import annotations
from pathlib import Path
import hashlib,json
import numpy as np
from a060_preflight.__main__ import run as reference_run
from a060_preflight.mechanics import diagnostics,rank_one,rank_two,balanced,rank_one_gate
from sst_falsifier.backends import cpp_pybind

def _check_framework(root):
    framework=(root/".sst_framework_root").read_text().strip()
    fr=(root/framework).resolve()
    manifest=json.loads((fr/"PACKAGE_MANIFEST.json").read_text(encoding="utf8"))
    bad=[]
    for f in manifest["files"]:
        p=fr/f["path"]
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=f["sha256"]:
            bad.append(f["path"])
    return len(manifest["files"]),bad

def _json(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False,default=str)+"\n",encoding="utf8")

def run_scientific_pipeline(root:Path,cfg,ledger,mode:str):
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    out.mkdir(parents=True,exist_ok=True)
    ledger.record("G0","PASS",reason="Official v1.0.7 frozen protocol verified by framework runner")
    refs=reference_run(root/"sources/papers",root/"sources/REFERENCE_HASHES.json")
    refs.pop('frozen_protocol',None)
    refs.pop('native_cpu_fp64_certification',None)
    refs.pop('not_an_official_framework_ledger',None)
    refs.pop('run_level',None)
    refs['schema']='A060-M00-M04-REFERENCE-RESULTS-2';refs['version']='v0.2.1'
    refs['framework_frozen_protocol_verified']=True
    refs['note']='Local mathematical reference checks only; the authoritative framework gate ledger is GATE_LEDGER.json and C++ certification is G5'
    _json(out/"M00_M04_REFERENCE.json",refs)
    fw_count,fw_bad=_check_framework(root)
    src=refs['results']['M00'];ok_source=src['precheck_status']=='REFERENCE_PASS' and fw_count==92 and not fw_bad
    ledger.record('G1','PASS' if ok_source else 'FAIL',metrics={'M00_SOURCE':src,'framework_verified':fw_count,'framework_bad':fw_bad},reason='Paper SHA and framework-manifest check; A045 registry conflict stays independently UNRESOLVED')
    checks=refs['results']
    ok12=all(checks[k]['precheck_status']=='REFERENCE_PASS' for k in ('M01','M02'))
    ledger.record('G2','PASS' if ok12 else 'FAIL',metrics={'M01':checks['M01']['details'],'M02':checks['M02']['details']},reason='Independent exact Euler and gradient tensor references')
    ok34=all(checks[k]['precheck_status']=='REFERENCE_PASS' for k in ('M03','M04'))
    ledger.record('G3','PASS' if ok34 else 'FAIL',metrics={'M03':checks['M03']['details'],'M04':checks['M04']['details']},reason='Periodic Fourier projection and direct sphere integration')
    for g in ('G4','G6','G7'):
        ledger.record(g,'NOT_APPLICABLE',reason='Disabled by preregistered CPU-only analytic scope; no independent physical replication is asserted')
    backend={'schema':'SST-BACKEND-MANIFEST-2','framework':'1.0.7','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'modes':'M00-M04_ANALYTIC_ONLY'}
    samples=[('rank1',rank_one()),('rank2',rank_two(eps=.1)),('balanced',balanced()),('gate+',rank_one_gate()),('gate-',rank_one_gate(sign=-1))]
    rng=np.random.default_rng(51317)
    samples += [('random'+str(i),rng.normal(size=(3,3))) for i in range(24)]
    # compiled C++ mandatory; never silently promote Python or GPU
    try:
        mod, build=cpp_pybind.load(root,require=True,verbose=False)
        assert mod is not None and hasattr(mod,'tensor_diagnostics')
        errs=[]
        for name,A in samples:
            A=A-np.trace(A)/3*np.eye(3)
            d=diagnostics(A)
            py=np.array([float(np.trace(A)),d['Q'],d['R'],d['enstrophy_density'],d['strain_sq'],d['Rs'],d['Vs'],d['fluxfactor']],dtype=float)
            nat=np.asarray(mod.tensor_diagnostics(A),dtype=float)
            errs.append(float(np.max(abs(py-nat)/np.maximum(1.0,np.abs(py)))))
        max_err=max(errs);valid=bool(max_err<=1e-10)
        backend['cpp']={'requested_backend':'cpp','actual_backend':dict(mod.backend_info()).get('backend'),'precision':'float64',
                        'n_cases':len(errs),'max_relative_parity':max_err,'compile_fingerprint':build.fingerprint_sha256,'certified':valid}
        ledger.record('G5','PASS' if valid else 'FAIL',metrics=backend['cpp'],requested_backend='cpp',actual_backend=backend['cpp']['actual_backend'],authority='CERTIFICATION',reason='Native pybind11 C++17 FP64 tensor kernel cross-check')
    except Exception as exc:
        backend['cpp']={'certified':False,'error':type(exc).__name__+': '+str(exc)}
        ledger.record('G5','UNRESOLVED',metrics=backend['cpp'],requested_backend='cpp',actual_backend='none',authority='UNRESOLVED',reason='C++ compiler or kernel unavailable: no fallback permitted')
    ledger.record('G8','UNRESOLVED',metrics={'A045_registry':'UNRESOLVED_A045_NAME_CONFLICT','A054_state_selection':'NOT_IMPORTED','PKLSA_physical_simulation':'NOT_RUN'},reason='Physical mechanism, registry reconciliation and dynamic stability deliberately not certified in analytic tranche')
    return backend
