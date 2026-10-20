"""A065 v0.3.4: independent historical *geometry seed* diagnostics.

No Euler PDE, no SST dimensional calibration, no knot stability, no Casimir/gravity.
DO NOT alter original D01/D02/D03 sealed inputs or v0.3.3 gate-routing.
Numerical workflow: native C++17 RK4 + independent Python RK4 spot parity.
"""
from __future__ import annotations
import hashlib, json, math, os, shutil, subprocess, tempfile
from pathlib import Path
from .pklsa import load_geometry
from .dynamics import evolve, rms_difference
from .independent_fremlin_v032 import run_native
from .security import canon

FORMULAS = {
  'A_Fourier_2015_p32': lambda t: (math.cos(t)+1.5*math.cos(2*t), math.sin(t)-1.5*math.sin(2*t), .35*math.sin(3*t)),
  'B_Torus_2015_p66': lambda t: ((2+math.cos(3*t))*math.cos(2*t), (2+math.cos(3*t))*math.sin(2*t), math.sin(3*t)),
}
DERIVATIVES = {
  'A_Fourier_2015_p32': lambda t: (-math.sin(t)-3*math.sin(2*t),math.cos(t)-3*math.cos(2*t),1.05*math.cos(3*t)),
  'B_Torus_2015_p66': lambda t: (-3*math.sin(3*t)*math.cos(2*t)-2*(2+math.cos(3*t))*math.sin(2*t),
                                  -3*math.sin(3*t)*math.sin(2*t)+2*(2+math.cos(3*t))*math.cos(2*t),3*math.cos(3*t)),
}

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _rms(a,b):return rms_difference(a,b)
def _relative(a,b,initial,step):
    numerator=_rms(a,b[::step]);denom=_rms(a,initial)
    return {'rms_absolute':numerator, 'coarse_displacement_rms':denom,
            'relative_to_coarse_displacement':numerator/max(denom,1e-14)}
def _geometry(points):
    n=len(points)
    edges=[math.dist(points[i],points[(i+1)%n]) for i in range(n)]
    length=sum(edges);mean=length/n
    return {'N':n,'polygon_length':length,'average_edge':mean,
            'edge_coefficient_variation':math.sqrt(sum((x-mean)**2 for x in edges)/n)/mean,
            'closure_edge':edges[-1], 'zero_duplicate_endpoint':math.dist(points[0],points[-1])>1e-8}
def _reference_curve_length(seed):
    # Independent high-order composite Simpson integral, not source regenerate.py.
    k=16384; h=2*math.pi/k;fn=DERIVATIVES[seed];total=0.
    for j in range(k+1):
        v=fn(j*h);speed=math.sqrt(sum(x*x for x in v));total+=(1 if j in (0,k) else 4 if j%2 else 2)*speed
    return total*h/3

def validate(root):
    root=Path(root);spec=json.loads((root/'preregistration/HISTORICAL_V034.json').read_text())
    prereg_digest=_sha(root/'preregistration/HISTORICAL_V034.json')
    official=root/'science_contract.json'
    if official.is_file():
        assumptions=json.loads(official.read_text(encoding='utf8')).get('assumptions',[])
        pinned=any('v0.3.4 historical geometry preregistration SHA256='+prereg_digest in x for x in assumptions)
    else:
        doc=root/'docs/HISTORICAL_V034_CONTRACT.md'
        pinned=doc.is_file() and f'Preregistration SHA256: `{prereg_digest}`' in doc.read_text(encoding='utf8')
    if not pinned:raise ValueError('HISTORICAL_V034_UNPINNED_OR_MUTATED_PREREGISTRATION')
    d=root/'data/HISTORICAL_2015';up=json.loads((d/'manifest.json').read_text())
    if spec['schema']!='A065-HISTORICAL-V034-PREREG-1' or spec['release']!='v0.3.4':raise ValueError('HISTORICAL_V034_PREREG_INVALID')
    for f,expected in spec['source_hashes'].items():
        p=d/f
        if not p.is_file() or _sha(p)!=expected:raise ValueError('HISTORICAL_SOURCE_HASH_MISMATCH:'+f)
    if _sha(d/'regenerate.py')!=spec['regenerator_hash'] or _sha(d/'manifest.json')!=spec['manifest_hash']:
        raise ValueError('HISTORICAL_GENERATOR_OR_MANIFEST_CHANGED')
    names=list(spec['seeds']);report={}
    for name in names:
        if name not in FORMULAS:raise ValueError('UNKNOWN_HISTORY_SEED')
        original=up['seeds'][name]
        dat={}
        for n in (600,1200):
            filename=f'{name}_N{n}_arclength.xyz'
            points=load_geometry(d/filename)
            if len(points)!=n:raise ValueError('INVALID_HISTORICAL_N')
            stats=_geometry(points)
            if not stats['zero_duplicate_endpoint'] or stats['edge_coefficient_variation']>1e-3:raise ValueError('INVALID_HISTORICAL_ARCLENGTH_OR_CLOSURE')
            if abs(stats['polygon_length']-original['files'][filename]['closed_polygon_length_nondim'])>1e-8:raise ValueError('POLYGON_LENGTH_MISMATCH')
            dat[n]=points
        raw600,raw1200=dat[600],dat[1200]
        anchor=max(math.dist(p,q) for p,q in zip(raw600,raw1200[::2]))
        if anchor>spec['max_600_1200_arc_alignment']:raise ValueError('HISTORY_ARC_ALIGNMENT_BAD')
        param_start=FORMULAS[name](0.0)
        if math.dist(raw600[0],param_start)>1e-12:raise ValueError('FORMULA_START_MISMATCH')
        analytic_length=_reference_curve_length(name)
        declared=original['analytic_arclength_nondim']
        if abs(analytic_length-declared)/declared>spec['analytic_length_relative_tolerance']:
            raise ValueError('HISTORICAL_PARAMETRIC_LENGTH_MISMATCH')
        report[name]={'coordinate_units':'dimensionless_unscaled','source_class':'HISTORICAL_PARAMETRIC_GEOMETRY_ONLY',
           'historic_page':original['historical_page'], 'formula':original['original_formula'],
           'N600':_geometry(raw600),'N1200':_geometry(raw1200),
           'max_600_vs_1200_subsample_distance':anchor,'parametric_length_independent':analytic_length,
           'manifest_parametric_length':declared,
           'raw_hashes':{str(n):_sha(d/f'{name}_N{n}_arclength.xyz') for n in (600,1200)},
           'not_pklsa_dynamically_relaxed':True}
    return report

def _native(root,records,spec):
    compiler=os.environ.get('CXX','g++')
    if not shutil.which(compiler):return {'status':'UNRESOLVED_COMPILER_MISSING','compiler':compiler}
    source=Path(root)/'native/fremlin_propagator.cpp'
    with tempfile.TemporaryDirectory(prefix='a065_historical_v034_') as td:
        exe=Path(td)/('historical.exe' if os.name=='nt' else 'historical')
        cp=subprocess.run([compiler,'-O2','-std=c++17',str(source),'-o',str(exe)],capture_output=True,text=True,timeout=120)
        if cp.returncode:return {'status':'FAIL_NATIVE_BUILD','compiler':compiler,'stderr':cp.stderr[-1200:]}
        answer={}
        for name in spec['seeds']:
            rootgeom=Path(root)/'data/HISTORICAL_2015'
            p1200=load_geometry(rootgeom/f'{name}_N1200_arclength.xyz')
            p600=load_geometry(rootgeom/f'{name}_N600_arclength.xyz')
            grids={150:p600[::4],300:p600[::2],600:p600,1200:p1200}
            T=spec['final_time'];gamma=spec['gamma'];steps=spec['rk4_steps'];eps=spec['epsilon']
            finals={n:run_native(exe,grids[n],steps,eps,T,gamma) for n in (150,300,600,1200)}
            pair={}
            for small,big in ((150,300),(300,600),(600,1200)):
                result=_relative(finals[small],finals[big],grids[small],big//small)
                result['threshold']=spec['spatial_threshold'];result['status']='PASS' if result['relative_to_coarse_displacement']<spec['spatial_threshold'] else 'FAIL'
                pair[f'{small}_vs_{big}']=result
            # Independent Python numerical reproduction tests actual time integrator.
            py=evolve(grids[150],eps,gamma,T,steps)
            parity=_rms(py,finals[150]);parity_ok=parity<spec['python_cpp_parity_absolute_tolerance']
            # Fixed *absolute* raw historical core values; not matched size or force.
            sensitivity={}
            for subeps in spec['other_epsilon_values']:
                trial=run_native(exe,grids[300],steps,subeps,T,gamma)
                diff=_rms(trial,finals[300]);displ=_rms(grids[300],finals[300])
                sensitivity[str(subeps)]={'rms_final_position_difference':diff,
                    'relative_to_baseline_displacement':diff/max(displ,1e-14)}
            # Independent temporal convergence at N300, comparing same T and different steps.
            final4=run_native(exe,grids[300],4,eps,T,gamma)
            final16=run_native(exe,grids[300],16,eps,T,gamma)
            tm4=_relative(final4,finals[300],grids[300],1)['relative_to_coarse_displacement']
            tm8=_relative(finals[300],final16,grids[300],1)['relative_to_coarse_displacement']
            answer[name]={'spatial':pair,'core_sensitivity':sensitivity,
              'python_cpp_parity_N150_rms':parity,'python_cpp_parity_status':'PASS' if parity_ok else 'FAIL',
              'temporal_N300_4_vs_8':tm4,'temporal_N300_8_vs_16':tm8,
              'temporal_status':'PASS' if max(tm4,tm8)<spec['temporal_threshold'] else 'FAIL',
              'spatial_status':'PASS' if all(r['status']=='PASS' for r in pair.values()) else 'FAIL',
              'epsilon_over_N600_mean_edge':eps/records[name]['N600']['average_edge'],
              'scope':'same reduced regularized filament ODE; native C++17 + Python parity, NOT Euler/PKLSA physical validation'}
    return {'status':'EXECUTED','compiler':compiler,'backend':'cpp17-fp64','source_sha256':_sha(source),'seeds':answer}

def run(root, *, persist=True):
    root=Path(root);spec=json.loads((root/'preregistration/HISTORICAL_V034.json').read_text())
    records=validate(root)
    data={'schema':'A065-HISTORICAL-RESULTS-V034-1','release':'v0.3.4',
      'precommit_sha256':_sha(root/'preregistration/HISTORICAL_V034.json'),
      'geometry_sources':records,'native_qualification':_native(root,records,spec),
      'old_G2':'FAIL_RETAINED','old_G10':'PASS_NOT_PROMOTED',
      'physical_euler':'UNRESOLVED','physical_casimir':'UNRESOLVED','physical_gravity':'UNRESOLVED',
      'no_new_independent_dynamic_pklsa_provider':True,
      'original_sealed_sources_unchanged':True}
    data['result_sha256']=hashlib.sha256(canon(data)).hexdigest()
    if persist:
        dst=root/'outputs/HISTORICAL_V034_RESULT.json';dst.parent.mkdir(exist_ok=True,parents=True)
        with dst.open('xb') as out:out.write(canon(data))
    return data
