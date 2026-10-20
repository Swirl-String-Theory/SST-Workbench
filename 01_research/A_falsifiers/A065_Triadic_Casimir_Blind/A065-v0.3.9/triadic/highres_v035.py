"""A065 v0.3.5 -- preregistered high-resolution DIRECT-PARAMETRIC trefoil test.

Evidence: dimensionless, reduced regularized vortex-filament ODE only.
Both geometries are historical initial curves, NOT independent dynamical PKLSA
providers. 2400/4800 XYZ files come from evaluating the analytic formulas at
uniform arc length, NOT interpolating N1200 XYZ or changing legacy seals.
"""
from __future__ import annotations
import hashlib,json,math,os,shutil,subprocess,tempfile,time
from pathlib import Path
from .security import canon
from .pklsa import load_geometry
from .dynamics import evolve,rms_difference
from .historical_v034 import validate as validate_v034, FORMULAS

SEEDS=('A_Fourier_2015_p32','B_Torus_2015_p66')


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rms(a,b):
    if len(a)!=len(b):raise ValueError('unequal length in trajectory comparison')
    return rms_difference(a,b)


def _write_exclusive(path, record):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8') as f:
        json.dump(record,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n')


def spec_validate(root):
    root=Path(root)
    specp=root/'preregistration/HIGHRES_V035.json'
    spec=json.loads(specp.read_text(encoding='utf8'))
    if spec['schema']!='A065-HIGHRES-V035-PREREG-1' or spec['version']!='v0.3.5':
        raise ValueError('HIGHRES_V035_PREREG_SCHEMA_INVALID')
    sh=_sha(specp)
    science=root/'science_contract.json'
    science_txt=json.dumps(json.loads(science.read_text(encoding='utf8')).get('assumptions',[])) if science.exists() else ''
    docs=root/'docs/HIGHRES_V035_CONTRACT.md'
    docs_txt=docs.read_text(encoding='utf8') if docs.exists() else ''
    if f'v0.3.5 high-resolution preregistration SHA256={sh}' not in science_txt and f'Preregistration SHA256: `{sh}`' not in docs_txt:
        raise ValueError('HIGHRES_V035_UNPINNED_OR_MUTATED_PREREGISTRATION')
    if spec['grids']!=[600,1200,2400,4800] or spec['core_epsilon_values']!=[.06,.12,.24] or spec['baseline_epsilon']!=.12:
        raise ValueError('HIGHRES_V035_UNAPPROVED_GRID_OR_CORE')
    if spec['gamma']!=1.0 or spec['T']!=.04 or spec['steps']!=8 or spec['relative_threshold']!=.01 or spec['temporal_threshold']!=.001:
        raise ValueError('HIGHRES_V035_UNAPPROVED_NUMERICAL_PARAMS')
    hist=validate_v034(root)
    d=root/'data/HISTORICAL_2015'
    all_points={}
    for name in SEEDS:
        all_points[name]={}
        for n in spec['grids']:
            filename=f'{name}_N{n}_arclength.xyz'
            expected=spec['xyz_sha256'][filename]
            path=d/filename
            if not path.is_file() or _sha(path)!=expected:
                raise ValueError('HIGHRES_XYZ_HASH_MISMATCH:'+filename)
            pts=load_geometry(path)
            if len(pts)!=n or math.dist(pts[0],FORMULAS[name](0.))>1e-12:
                raise ValueError('HIGHRES_PARAMETRIC_GEOMETRY_INVALID:'+filename)
            all_points[name][n]=pts
        for n in [600,1200,2400]:
            coarse,fine=all_points[name][n],all_points[name][2*n]
            deviation=max(math.dist(a,b) for a,b in zip(coarse,fine[::2]))
            if deviation>spec['max_nested_xyz_mismatch']:
                raise ValueError('HIGHRES_NON_NESTED_ARCLENGTH_GRID:'+name+':'+str(n))
        # No geometry scaling to mimic different physics between two distinct curves.
    return spec,sh,all_points,hist


def _compile(root,compiler,td):
    src=Path(root)/'native/highres_filament_v035.cpp'
    if _sha(src)!=json.loads((Path(root)/'preregistration/HIGHRES_V035.json').read_text())['cpp_source_sha256']:
        raise ValueError('HIGHRES_CPP_SOURCE_HASH_MISMATCH')
    if not shutil.which(compiler):return None,{'status':'UNRESOLVED_COMPILER_MISSING','compiler':compiler}
    exe=Path(td)/('a065_highres.exe' if os.name=='nt' else 'a065_highres')
    extra=os.environ.get('A065_HIGHRES_CPP_EXTRAFLAGS','').strip()
    if extra:
        raise ValueError('UNREGISTERED_COMPILER_FLAGS_NOT_ALLOWED')
    trials=[]
    for openmp in (True,False):
        cmd=[compiler,'-O3','-std=c++17']+(['-fopenmp'] if openmp else [])+[str(src),'-o',str(exe)]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        trials.append({'command':cmd,'returncode':p.returncode,'compiler_error_tail':p.stderr[-500:]})
        if p.returncode==0:
            return exe,{'status':'COMPILED','compiler':compiler,'openmp_enabled':openmp,'command':cmd,'compiler_trials':trials,
                        'cpp_sha256':_sha(src),'exe_sha256':_sha(exe)}
    return None,{'status':'UNRESOLVED_COMPILER_BUILD_FAILED','compiler':compiler,'compiler_trials':trials}


def _native_run(exe,vertices,eps,spec,steps=None,threads=4):
    steps=spec['steps'] if steps is None else steps
    n=len(vertices)
    data=f'{n} {eps:.17g} {spec["gamma"]:.17g} {spec["T"]:.17g} {steps}\n'+''.join(
        f'{v[0]:.17g} {v[1]:.17g} {v[2]:.17g}\n' for v in vertices)
    env=os.environ.copy();env['OMP_NUM_THREADS']=str(threads);env['OMP_DYNAMIC']='FALSE'
    t=time.monotonic()
    p=subprocess.run([str(exe)],input=data,capture_output=True,text=True,env=env,timeout=240)
    if p.returncode:raise RuntimeError(f'HIGHRES_NATIVE_RUN_FAILED N={n} eps={eps}: returncode={p.returncode}: {p.stderr[-500:]}')
    out=[tuple(map(float,line.split())) for line in p.stdout.splitlines()]
    if len(out)!=n or any(len(row)!=3 or not all(math.isfinite(z) for z in row) for row in out):
        raise RuntimeError('HIGHRES_NATIVE_TRAJECTORY_MALFORMED')
    return out,time.monotonic()-t


def _relative(a,b,initial,step):
    diff=_rms(a,b[::step]);disp=_rms(initial,a)
    if disp<1e-12:return {'rms_difference':diff,'coarse_rms_displacement':disp,'relative_error':None,'status':'UNRESOLVED_ZERO_MOTION'}
    return {'rms_difference':diff,'coarse_rms_displacement':disp,'relative_error':diff/disp}


def _native(root,spec,points):
    compiler=os.environ.get('CXX','g++')
    with tempfile.TemporaryDirectory(prefix='a065_highres_v035_') as td:
        exe,bld=_compile(root,compiler,td)
        if exe is None:return {'status':bld['status'],'build':bld}
        threads_raw=os.getenv('A065_THREADS','4')
        if not threads_raw.isdigit() or int(threads_raw)<1 or int(threads_raw)>64:
            raise ValueError('A065_THREADS must be an integer in [1,64]')
        threads=int(threads_raw)
        by_seed={}
        for name in SEEDS:
            geom=points[name];eps_results={}
            for eps in spec['core_epsilon_values']:
                trials={};total=0.
                for n in spec['grids']:
                    trajectory,elapsed=_native_run(exe,geom[n],eps,spec,threads=threads)
                    trials[n]=trajectory;total+=elapsed
                pairs={}
                for n in spec['grids'][:-1]:
                    raw=_relative(trials[n],trials[2*n],geom[n],2)
                    r=raw['relative_error']
                    raw.update({'threshold_1pct':spec['relative_threshold'],
                                'status_1pct':'PASS' if r is not None and r<spec['relative_threshold'] else 'FAIL' if r is not None else 'UNRESOLVED',
                                'status_0p1pct':'PASS' if r is not None and r<spec['reporting_target_0p1pct'] else 'FAIL' if r is not None else 'UNRESOLVED'})
                    pairs[f'{n}_vs_{2*n}']=raw
                eps_results[f'{eps:.2f}']={'pairs':pairs,'native_wall_seconds_observed':round(total,6),
                    'all_1pct':'PASS' if all(v['status_1pct']=='PASS' for v in pairs.values()) else 'FAIL',
                    'source':'same direct parametric historical geometry (NOT independent physical observations)'}
            # Independent Python vs C++ FP64 for full RK4 on a testable subset,
            # not an assertion of 4800-node Python parity.
            small=geom[600][::4]
            out_small,_=_native_run(exe,small,spec['baseline_epsilon'],spec,threads=threads)
            py=evolve(small,spec['baseline_epsilon'],spec['gamma'],spec['T'],spec['steps'])
            parity=_rms(py,out_small)
            # OpenMP thread count cannot change same-node summation order.
            omp_small,_=_native_run(exe,small,spec['baseline_epsilon'],spec,threads=1)
            threaded=_rms(omp_small,out_small)
            time_checks={}
            for n in spec['temporal_grids']:
                y4,sec4=_native_run(exe,geom[n],spec['baseline_epsilon'],spec,steps=4,threads=threads)
                y8,sec8=_native_run(exe,geom[n],spec['baseline_epsilon'],spec,steps=8,threads=threads)
                y16,sec16=_native_run(exe,geom[n],spec['baseline_epsilon'],spec,steps=16,threads=threads)
                p4=_relative(y4,y8,geom[n],1);p8=_relative(y8,y16,geom[n],1)
                good=all(p['relative_error'] is not None and p['relative_error']<spec['temporal_threshold'] for p in (p4,p8))
                time_checks[str(n)]={'4_vs_8':p4,'8_vs_16':p8,'status':'PASS' if good else 'FAIL',
                                     'wall_seconds':round(sec4+sec8+sec16,6)}
            seed_stats={}
            for n in spec['grids']:
                edges=[math.dist(geom[n][i],geom[n][(i+1)%n]) for i in range(n)]
                seed_stats[str(n)]={'mean_edge':sum(edges)/n,'edge_over_eps_baseline':sum(edges)/n/spec['baseline_epsilon']}
            baseline=eps_results[f'{spec["baseline_epsilon"]:.2f}']
            by_seed[name]={'epsilon_ladders':eps_results,'geometry':seed_stats,
               'baseline_spatial_1pct':baseline['all_1pct'],
               'parity_N150_python_cpp_rms':parity,
               'parity_N150_serial_parallel_rms':threaded,
               'parity_status':'PASS' if parity<spec['python_cpp_parity_abs_threshold'] and threaded<spec['thread_parity_abs_threshold'] else 'FAIL',
               'temporal_controls':time_checks,
               'temporal_status':'PASS' if all(k['status']=='PASS' for k in time_checks.values()) else 'FAIL'}
        return {'status':'EXECUTED','build':bld,'threads':threads,'backend':'cpp17-fp64-openmp-optional','seeds':by_seed,
                'physical_interpretation':'NUMERICAL_REDUCED_FILAMENT_ODE_ONLY'}


def run(root,persist=True):
    root=Path(root)
    spec,prereg_hash,points,historical=spec_validate(root)
    outfile=root/'outputs/HIGHRES_V035_RESULT.json'
    if outfile.exists():
        o=json.loads(outfile.read_text(encoding='utf8'))
        check=dict(o);expected=check.pop('result_sha256',None)
        if expected!=hashlib.sha256(canon(check)).hexdigest() or o.get('prereg_sha256')!=prereg_hash or o.get('schema')!='A065-HIGHRES-V035-RESULT-1':
            raise ValueError('CACHED_HIGHRES_RESULT_INTEGRITY_FAILURE')
        if o.get('source_sha256')!=spec['xyz_sha256']:
            raise ValueError('CACHED_HIGHRES_SOURCE_HASH_FAILURE')
        return o
    native=_native(root,spec,points)
    o={'schema':'A065-HIGHRES-V035-RESULT-1','version':'v0.3.5','prereg_sha256':prereg_hash,
       'source_sha256':spec['xyz_sha256'],'native':native,
       'legacy_G2':'FAIL_RETAINED','legacy_G13':'FAIL_RETAINED','old_source_seals':'UNCHANGED',
       'physical_euler':'UNRESOLVED','physical_pklsa':'UNRESOLVED','physical_casimir':'UNRESOLVED','physical_gravity':'UNRESOLVED',
       'independent_physical_provider_count':0,'no_target_fit':True,'reveal_performed':False}
    o['result_sha256']=hashlib.sha256(canon(o)).hexdigest()
    if persist:_write_exclusive(outfile,o)
    return o
