"""A065 v0.3.6: generate historical trefoil meshes INSIDE the falsifier.

Original input XYZ is immutable, hashed and independently compared. The original
2015 analytic equations are sampled freshly at runtime using only stdlib.
One preregistered fixed epsilon (0.06) is forwarded to C++17 RK4, while the
mean segment / epsilon ratio is recorded at all mesh resolutions. This is a
numerical discretization check and does NOT infer a physical SST core radius.
"""
from __future__ import annotations
import hashlib,json,math,os,tempfile
from pathlib import Path
from .security import canon,verify_all
from .pklsa import load_geometry
from .parametric_generator_v036 import SEEDS,prepare,sample
from .highres_v035 import spec_validate,_compile,_native_run,_relative

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _write_json_new(p,data):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2,ensure_ascii=False,sort_keys=True);f.write('\n')

def _geometry(pts,epsilon):
    edges=[math.dist(p,pts[(i+1)%len(pts)]) for i,p in enumerate(pts)]
    mean=sum(edges)/len(edges)
    spread=math.sqrt(sum((e-mean)**2 for e in edges)/len(edges))/mean
    return {'N':len(pts),'polygon_arclength':sum(edges),'mean_segment':mean,
            'segment_cv':spread,'segment_over_epsilon':mean/epsilon,
            'epsilon_over_segment':epsilon/mean,'max_segment_over_epsilon':max(edges)/epsilon}

def validate(root):
    root=Path(root);pre=root/'preregistration/GENERATED_V036.json'
    cfg=json.loads(pre.read_text(encoding='utf8'));prereg_hash=_sha(pre)
    science=root/'science_contract.json'
    if science.is_file():
        declared=json.dumps(json.loads(science.read_text(encoding='utf8')).get('assumptions',[]))
    else:
        declared=(root/'docs/GENERATED_V036_CONTRACT.md').read_text(encoding='utf8')
    if prereg_hash not in declared:
        raise ValueError('V036_UNPINNED_PREREGISTRATION')
    if cfg.get('schema')!='A065-GENERATED-V036-PREREG-1' or cfg.get('version')!='v0.3.6':raise ValueError('V036_SCHEMA_INVALID')
    if cfg.get('generator_impl_sha256')!=_sha(root/'triadic/parametric_generator_v036.py'):raise ValueError('V036_GENERATOR_HASH_CHANGED')
    if cfg.get('historical_script_sha256')!=_sha(root/'data/HISTORICAL_2015/regenerate.py'):raise ValueError('V036_HISTORICAL_SOURCE_SCRIPT_CHANGED')
    if cfg.get('v035_prereg_sha256')!=_sha(root/'preregistration/HIGHRES_V035.json'):raise ValueError('V036_PARENT_PREREG_CHANGED')
    if (cfg.get('grids')!=[600,1200,2400,4800] or cfg.get('fixed_epsilon')!=0.06 or
        cfg.get('gamma')!=1. or cfg.get('T')!=.04 or cfg.get('steps')!=8 or
        cfg.get('fine_pair_threshold')!=.01 or cfg.get('reporting_segment_ratio_threshold')!=.25 or
        cfg.get('generator_grid_n')!=262144 or cfg.get('max_coordinate_deviation')!=1e-7):
        raise ValueError('V036_UNREGISTERED_PARAMETERS')
    spec,_,original,_=spec_validate(root)   # checks ALL original hashes and nested meshes
    if spec['cpp_source_sha256']!=_sha(root/'native/highres_filament_v035.cpp'):
        raise ValueError('V036_NATIVE_SOURCE_CHANGED')
    # Source seals checked even for a generator-only run.
    verify_all(root)
    return cfg,prereg_hash,original,spec

def generate(root, cfg, original, write_xyz=False):
    root=Path(root)
    out={};coordinates={};worst=0.
    for seed in SEEDS:
        prepared=prepare(seed)
        by_n={};by_xyz={}
        for n in cfg['grids']:
            pts=sample(prepared,n)
            deviation=max(math.dist(a,b) for a,b in zip(pts,original[seed][n]))
            worst=max(worst,deviation)
            g=_geometry(pts,cfg['fixed_epsilon'])
            by_n[str(n)]={'max_diff_from_sealed_xyz':deviation,**g}
            if g['segment_cv']>cfg['max_segment_cv'] or deviation>cfg['max_coordinate_deviation']:
                raise ValueError(f'V036_GENERATED_SOURCE_MISMATCH:{seed}:N{n}')
            by_xyz[n]=pts
            if write_xyz:
                path=root/'outputs/GENERATED_V036_XYZ'/f'{seed}_N{n}_generated.xyz'
                path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('x',encoding='ascii',newline='\n') as fh:
                    for x,y,z in pts:fh.write(f'{x:.17e} {y:.17e} {z:.17e}\n')
                by_n[str(n)]['regenerated_xyz_sha256']=_sha(path)
        for n in cfg['grids'][:-1]:
            delta=max(math.dist(a,b) for a,b in zip(by_xyz[n],by_xyz[2*n][::2]))
            by_n[str(n)]['max_nested_difference']=delta
            if delta>cfg['max_coordinate_deviation']:raise ValueError('V036_NON_NESTED_REGENERATION')
        out[seed]={'curve_length_analytic_numeric':prepared['arclength'],'grids':by_n}
        coordinates[seed]=by_xyz
    return out,coordinates,worst

def run(root, persist=True):
    root=Path(root)
    cfg,prereg_hash,original,spec=validate(root)
    result_path=root/'outputs/GENERATED_V036_RESULT.json'
    if persist and result_path.exists():
        value=json.loads(result_path.read_text(encoding='utf8'))
        d=dict(value);claimed=d.pop('result_sha256',None)
        if claimed!=hashlib.sha256(canon(d)).hexdigest() or value['prereg_sha256']!=prereg_hash:
            raise ValueError('V036_CACHED_RESULT_INVALID')
        return value
    geom,pts,worst=generate(root,cfg,original,write_xyz=persist)
    threads=int(os.environ.get('A065_THREADS','4'))
    if threads<1 or threads>64:raise ValueError('INVALID_THREAD_COUNT')
    with tempfile.TemporaryDirectory(prefix='a065_v036_') as t:
        exe,bld=_compile(root,os.environ.get('CXX','g++'),t)
        if exe is None:
            dynamics={'status':'UNRESOLVED_NATIVE_BACKEND','build':bld}
        else:
            evals={}
            for seed in SEEDS:
                traj={}
                for n in cfg['grids']:
                    output,_=_native_run(exe,pts[seed][n],cfg['fixed_epsilon'],spec,steps=cfg['steps'],threads=threads)
                    traj[n]=output
                pairs={}
                for n in cfg['grids'][:-1]:
                    comp=_relative(traj[n],traj[2*n],pts[seed][n],2)
                    error=comp['relative_error']
                    comp['pass_1pct']=error is not None and error<cfg['fine_pair_threshold']
                    comp['legacy_coarse_pair_diagnostic_only']=n==600
                    pairs[f'{n}_vs_{2*n}']=comp
                evals[seed]={'pairs':pairs,'fine_pairs_pass_1pct':all(
                    p['pass_1pct'] for key,p in pairs.items() if not p['legacy_coarse_pair_diagnostic_only'])}
            dynamics={'status':'EXECUTED','backend':'native_c++17_fp64_openmp_optional',
                      'compiler':bld['compiler'],'openmp_enabled':bld['openmp_enabled'],
                      'threads':threads,'fixed_epsilon':cfg['fixed_epsilon'],'seeds':evals}
    v={'schema':'A065-GENERATED-V036-RESULT-1','version':'v0.3.6','prereg_sha256':prereg_hash,
       'source_generator_sha256':cfg['historical_script_sha256'],
       'generated_compatibility_max_xyz_difference':worst,'generated_geometry':geom,
       'dynamics':dynamics,'source_group_count':2,'independent_physical_provider_count':0,
       'regularization_interpretation':'dimensionless numerical smoothing epsilon, fixed across all N; not r_c',
       'physical_euler':'UNRESOLVED','physical_casimir':'UNRESOLVED','physical_gravity':'UNRESOLVED',
       'historical_G2':'FAIL_RETAINED','historical_G11':'FAIL_RETAINED','historical_G13':'FAIL_RETAINED',
       'no_target_fit':True,'revealed':False}
    v['result_sha256']=hashlib.sha256(canon(v)).hexdigest()
    if persist:_write_json_new(result_path,v)
    return v

def make_report(root,result):
    from .report_pdf import _pdf_text
    root=Path(root);lines=[('h1','A065 v0.3.6 - Analytic generator and epsilon audit'),
      ('normal','BLIND; geometric and numerical diagnostic only. No Euler/Casimir/gravity closure.'),
      ('h2','Core smoothing'),('normal','Regularized segment kernel: (distance^2 + epsilon^2)^(-3/2). epsilon=0.06 is a dimensionless smoothing scale in the original historical curve coordinate units; not a derived SST radius.'),
      ('normal','Gamma=1, T=0.04 and RK4 steps=8 fixed. Mesh refinement changes N, never epsilon.'),
      ('h2','Runtime-generated historical trefoils'),('normal',f"Independent direct generator vs pinned originals: max coordinate discrepancy {result['generated_compatibility_max_xyz_difference']:.3e}"),
      ('normal','The original SciPy regenerate.py is preserved and hashed; the falsifier uses equivalent stdlib arc-length inversion with independent comparison to sealed XYZ.')]
    for seed,d in result['generated_geometry'].items():
        lines.append(('h2',seed))
        for n,details in d['grids'].items():
            lines.append(('normal',f"N={n}: mean ds={details['mean_segment']:.8g}, ds/eps={details['segment_over_epsilon']:.6g}, edge CV={details['segment_cv']:.3e}"))
        if result['dynamics']['status']=='EXECUTED':
            for k,v in result['dynamics']['seeds'][seed]['pairs'].items():
                lines.append(('normal',f"{k}: relative error={v['relative_error']*100:.6g} %, 1pct pass={v['pass_1pct']}; 600vs1200 is a diagnostic, not fine-pair veto."))
    lines.extend([('h2','Falsifier gate policy'),('normal','G19 = analytic regenerated vs pinned XYZ. G20 = dimensionless ds/epsilon diagnostic; 0.25 at N4800 only. G21 = native generated epsilon=0.06 1200->2400 and 2400->4800 spatial comparison under 1pct.'),
       ('normal','Do not infer physical r_c from epsilon. All historic FAIL statuses and reveal block remain.'),('small',f"prereg_sha256: {result['prereg_sha256']}")])
    path=root/'reports'/'A065_v0.3.6_GENERATED_CORE_REPORT.pdf'
    pages=_pdf_text(path,lines)
    return {'path':str(path),'pages':pages}
