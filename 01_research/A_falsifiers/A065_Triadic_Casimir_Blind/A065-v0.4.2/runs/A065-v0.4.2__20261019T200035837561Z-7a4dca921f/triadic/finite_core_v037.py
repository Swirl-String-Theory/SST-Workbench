"""A065 v0.3.7: strictly synthetic, source-separated finite-vorticity-core inference.

No geometry-only source contains a transverse vorticity field. Recover a *profile-
conditional* length from circulation and cross-sectional enstrophy, and make
parameter-free predictions on precommitted held-out radii. The Rosenhead
kernel is deliberately not re-fitted on held-out velocity or pressure.

Physical core and PKLSA/Euler dynamical closure: UNRESOLVED.
"""
from __future__ import annotations
import hashlib, json, math, os, shutil, subprocess, tempfile
from pathlib import Path
from .security import verify_all
PI=math.pi

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_new(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')

def inferred_a(model,gamma,enstrophy):
    if model not in ('gaussian','rankine') or gamma<=0 or enstrophy<=0:raise ValueError('INVALID_CORE_INVARIANTS')
    factor=2 if model=='gaussian' else 1
    return gamma/math.sqrt(factor*PI*enstrophy)

def v_profile(model,gamma,a,r):
    if min(gamma,a,r)<=0:raise ValueError('INVALID_PROFILE_ARGUMENT')
    fractional=-math.expm1(-(r/a)**2) if model=='gaussian' else min((r/a)**2,1.)
    return gamma*fractional/(2*PI*r)

def v_rosenhead(gamma,eps,r):
    return gamma*r/(2*PI*(r*r+eps*eps))

def rms_relative(pred,observed):
    return math.sqrt(sum((p-q)**2 for p,q in zip(pred,observed))/sum(q*q for q in observed))

def validate(root):
    root=Path(root)
    cfgfile=root/'preregistration/FINITE_CORE_V037.json'
    cfg=json.loads(cfgfile.read_text(encoding='utf-8'))
    prehash=sha(cfgfile)
    science_path=root/'science_contract.json'
    if science_path.is_file():
        sci=json.loads(science_path.read_text(encoding='utf-8'))
        declared='\n'.join(str(x) for x in sci.get('assumptions',[]))
        if ('v0.3.7 finite-core' not in declared or prehash not in declared):
            raise ValueError('V037_UNPINNED_PREREGISTRATION')
    else:
        doc=(root/'docs/FINITE_CORE_V037_CONTRACT.md').read_text(encoding='utf-8')
        if 'FINITE_CORE_V037_PREREG_SHA256='+prehash not in doc:
            raise ValueError('V037_UNPINNED_PREREGISTRATION')
    if cfg.get('schema')!='A065-V037-FINITE-CORE-PREREG-1' or cfg.get('version')!='v0.3.7':raise ValueError('V037_PROTOCOL_SCHEMA')
    if cfg.get('models')!=['gaussian','rankine'] or cfg.get('source_class')!='synthetic_analytic_controls':raise ValueError('V037_MODEL_CHANGE')
    if cfg.get('holdout_swirl_relative_threshold')!=0.05 or cfg.get('holdout_pressure_relative_threshold')!=0.05 or cfg.get('kernel_mapping_discrepancy_min')!=0.1 or cfg.get('recovery_tolerance')!=1e-10:raise ValueError('V037_THRESHOLDS_CHANGED')
    if cfg['source_sha256']!=sha(root/cfg['source_file']):raise ValueError('V037_SOURCE_HASH_MISMATCH')
    if cfg['python_source_sha256']!=sha(root/'triadic/finite_core_v037.py'):raise ValueError('V037_PYTHON_SOURCE_CHANGED')
    if cfg['cpp_source_sha256']!=sha(root/'native/finite_core_v037.cpp'):raise ValueError('V037_NATIVE_SOURCE_CHANGED')
    if cfg['parent_v036_prereg_sha256']!=sha(root/'preregistration/GENERATED_V036.json'):raise ValueError('V037_PARENT_PREREG_CHANGED')
    verify_all(root)
    data=json.loads((root/cfg['source_file']).read_text(encoding='utf-8'))
    if data.get('schema')!='A065-V037-ANALYTIC-CONTROLS-1' or len(data.get('cases',[]))!=6:raise ValueError('V037_SOURCE_SCHEMA')
    return cfg,prehash,data

def _run_native(root,cases,amap,epsmap):
    exe_name=os.environ.get('CXX','').strip()
    if exe_name:
        cxx=shutil.which(exe_name)
    else:
        cxx=next((shutil.which(n) for n in ('g++','clang++') if shutil.which(n)),None)
    if not cxx:return {'status':'UNRESOLVED_NO_CXX','pairs_compared':0}
    with tempfile.TemporaryDirectory(prefix='a065_v037_') as d:
        exe=Path(d)/('finite_core.exe' if os.name=='nt' else 'finite_core')
        proc=subprocess.run([cxx,'-std=c++17','-O2',str(root/'native/finite_core_v037.cpp'),'-o',str(exe)],capture_output=True,text=True,timeout=90)
        if proc.returncode:raise RuntimeError('V037_NATIVE_COMPILE_FAILURE: '+proc.stderr[-1500:])
        lines=[];expected=[]
        for case in cases:
            key=case['id'];g=case['circulation'];z=case['enstrophy_per_length'];a=amap[key];eps=epsmap[key]
            for o in case['heldout_radial']:
                r=o['r'];lines.append(f'{case["model"]} {g:.17g} {z:.17g} {r:.17g}\n')
                expected.append((a,v_profile(case['model'],g,a,r),v_rosenhead(g,eps,r)))
        run=subprocess.run([str(exe)],input=''.join(lines),capture_output=True,text=True,timeout=60)
        if run.returncode:raise RuntimeError('V037_NATIVE_RUN_FAILURE: '+run.stderr[-1500:])
        got=run.stdout.strip().splitlines()
        if len(got)!=len(expected):raise RuntimeError('V037_NATIVE_COUNT_MISMATCH')
        diff=max(abs(float(a)-b) for row,xyz in zip(got,expected) for a,b in zip(row.split(),xyz))
        return {'status':'PASS' if diff<=5e-13 else 'FAIL','max_component_difference':diff,'pairs_compared':len(expected),'compiler':str(cxx),'authority':'CLOSED_FORM_KERNEL_ONLY'}

def run(root,persist=True,require_native=False):
    root=Path(root);cfg,prehash,data=validate(root)
    cases=data['cases'];rows=[];amap={};epsmap={};max_recovery=0.
    for case in cases:
        model=case['model'];g=float(case['circulation']);z=float(case['enstrophy_per_length']);rho=case['density']
        a=inferred_a(model,g,z) # only train observables: Gamma, Z, assumed profile
        eps_slope=a # match limit v_theta / r at origin to Rosenhead
        eps_half=a*(math.sqrt(math.log(2)) if model=='gaussian' else 1/math.sqrt(2))
        epsmap[case['id']]=eps_slope;amap[case['id']]=a
        obs=case['heldout_radial'];rs=[x['r'] for x in obs]
        y=[x['v_theta'] for x in obs]
        p=[x['pressure_gradient'] for x in obs]
        true_v=[v_profile(model,g,a,r) for r in rs]
        reg_v=[v_rosenhead(g,eps_slope,r) for r in rs]
        true_pg=[rho*v*v/r for v,r in zip(true_v,rs)]
        reg_pg=[rho*v*v/r for v,r in zip(reg_v,rs)]
        positive_v=rms_relative(true_v,y);positive_p=rms_relative(true_pg,p)
        observed_error=rms_relative(reg_v,y)
        pressure_error=rms_relative(reg_pg,p)
        negative_control_err=rms_relative([v_profile('rankine' if model=='gaussian' else 'gaussian',g,inferred_a('rankine' if model=='gaussian' else 'gaussian',g,z),r) for r in rs],y)
        max_recovery=max(max_recovery,positive_v,positive_p)
        rows.append({'id':case['id'],'assumed_core_profile':model,'Gamma':g,'enstrophy_cross_section':z,
            'a_derived_from_Gamma_and_Z':a,'epsilon_from_near_axis_slope':eps_slope,
            'epsilon_from_half_circulation':eps_half,
            'epsilon_mapping_relative_difference':abs(eps_slope-eps_half)/eps_slope,
            'positive_control_swirl_relative_RMS':positive_v,
            'positive_control_pressure_gradient_relative_RMS':positive_p,
            'rosenhead_swirl_heldout_relative_RMS':observed_error,
            'rosenhead_pressure_gradient_heldout_relative_RMS':pressure_error,
            'wrong_profile_negative_control_swirl_relative_RMS':negative_control_err,
            'holdout_points':len(rs),'holdout_used_for_core_derivation':False,
            'pressure_holdout_is_independent_measurement':False})
    assert len(rows)==6
    native=_run_native(root,cases,amap,epsmap)
    if require_native and native['status']!='PASS':raise RuntimeError('V037_NATIVE_PARITY_REQUIRED')
    recovered=max_recovery<=cfg['recovery_tolerance']
    representable=all(r['rosenhead_swirl_heldout_relative_RMS']<=cfg['holdout_swirl_relative_threshold'] and r['rosenhead_pressure_gradient_heldout_relative_RMS']<=cfg['holdout_pressure_relative_threshold'] for r in rows)
    ambiguous=all(r['epsilon_mapping_relative_difference']>cfg['kernel_mapping_discrepancy_min'] for r in rows)
    wrong_controls=all(r['wrong_profile_negative_control_swirl_relative_RMS']>cfg['holdout_swirl_relative_threshold'] for r in rows)
    result={'schema':'A065-V037-FINITE-CORE-RESULT-1','release':'v0.3.7','prereg_sha256':prehash,'synthetic_data_sha256':cfg['source_sha256'],
      'G22':'PASS','G23':'PASS' if recovered and wrong_controls else 'FAIL',
      'G24':'PASS' if representable else 'FAIL',
      'G25':'PASS' if ambiguous else 'FAIL',
      'G26':native['status'],'G27':'UNRESOLVED_NO_QUALIFIED_PHYSICAL_CORE_PROVIDER',
      'physical_euler':'UNRESOLVED','sst_rc_connection':'UNRESOLVED','physical_casimir_gravity':'UNRESOLVED',
      'core_measurement':'NOT_PROVIDED','core_profile_assumption_required':True,
      'no_fitted_epsilon':True,'no_heldout_fitting':True,'source_independence':'SYNTHETIC_ONLY',
      'native':native,'cases':rows,'max_analytic_positive_control_relative_error':max_recovery,
      'note':'Every sample is an analytic cross section, not a measured Euler/PKLSA vorticity field. Pressure-gradient holdout is algebraically derived from the same synthetic velocity and not independently measured.'}
    if persist:write_new(root/'outputs/FINITE_CORE_V037_RESULT.json',result)
    return result
