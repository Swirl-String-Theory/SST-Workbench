#!/usr/bin/env python3
"""A003 v0.3.0: E010 v0.3.1 native source-contract registration + C005 v0.6.1 RK4 filament evolution.

No source trees are modified.  Native E010 Workbench resolves an immutable runtime contract
containing the atlas, then 8 independently hashed resolution-specific carrier entries are emitted.
A full Euler solution/physical core model is NOT implied by a regularized filament ODE.
"""
from __future__ import annotations
import argparse, hashlib, importlib, importlib.util, json, math, os, secrets, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from a003_diagnostic_v027 import load_framework, json_write
from g6_pklsa_pilot_v029 import (source_check,g5_check,find_g5_summary,find_workbench,
     provider_check,finite_core_field,E010_REL,C005_REL,FRAMEWORK_REL,EXPECTED_MANIFEST)
from fourier_atlas_adapter import resolve_atlas_root,sha256_file,read_xyz,safe_atlas_file

VERSION='0.3.0'
SCHEMA='sst.a003.pklsa-g6-temporal/2'
SEEDS=('fibonacci_torus_F3','fibonacci_torus_F4')
SOURCE_ID='a003.fourier_torus.f3_f4.v0.1.2'


def carrier_rows(atlas,registry):
    rows=[]
    for sid in SEEDS:
        for n in (1200,2400,4800,9600):
            matches=[r for r in registry['records'] if r['id']==sid and r['points']==n and r['sampling']=='uniform_t']
            if len(matches)!=1:raise RuntimeError('not exactly one geometry for '+sid+' '+str(n))
            r=matches[0];src=safe_atlas_file(atlas,r['file'])
            digest=sha256_file(src)
            if digest!=r['sha256']:raise RuntimeError('source hash mismatch '+str(src))
            rows.append({'carrier_id':f'{SOURCE_ID}:{sid}:uniform_t:N{n}',
                         'source_id':SOURCE_ID,'source_file':str(src),
                         'atlas_relative_file':str(r['file']).replace('\\','/'),
                         'sha256':digest,'points':n,'sampling':'uniform_t','analytic_seed':sid,
                         'declared_torus_pair':[2,3] if sid.endswith('F3') else [3,5],
                         'independence_group':f'A003_ANALYTIC_GEOMETRY_{sid}',
                         'evidence_role':'generated_analytic_seed_not_independent_empirical_geometry',
                         'topology_not_certified':True})
    return rows


def register_e010(atlas,registry,wb,e010,out):
    """Call the actual E010 Workbench resolver, never infer registration from a marker file."""
    if not wb or not e010:return {'status':'UNRESOLVED','reason':'Workbench/E010 root not configured'}
    init=e010/'sst_pklsa'/'__init__.py';core=e010/'sst_pklsa'/'core.py'
    c1=e010/'configs'/'source_contract_production_v2.json'
    c2=e010/'configs'/'source_contract_v1.json'
    source_contract=c1 if c1.is_file() else c2
    if not all(p.is_file() for p in (init,core,source_contract)):
        return {'status':'UNRESOLVED','reason':'native E010 core/init/config contract missing',
                'required':[str(init),str(core),str(source_contract)]}
    try:
        rel=atlas.resolve().relative_to(wb.resolve()).as_posix()
    except ValueError:
        return {'status':'UNRESOLVED','reason':'A003 source is outside Workbench; requires canonical relative path'}
    contract=json.loads(source_contract.read_text(encoding='utf-8'))
    if not isinstance(contract.get('sources'),list):raise RuntimeError('E010 source contract has no sources array')
    existing=[x for x in contract['sources'] if x.get('source_id')==SOURCE_ID]
    if existing:raise RuntimeError('E010 source id collision; fail closed')
    spec={'source_id':SOURCE_ID,'kind':'geometry_atlas','role':'generated_analytic_geometry_seed',
          'provider_group':'a003_analytic_seed_atlas','method_group':'a003_fourier_torus',
          'canonical_paths':[rel],'legacy_globs':[],'admit_geometry':True,'required':True,
          'independence_policy':'F3/F4 synthetic analytic families; all resolutions within family correlated'}
    contract['sources'].append(spec)
    contract_file=out/'E010_A003_RUNTIME_SOURCE_CONTRACT.json'
    json_write(contract_file,contract)
    # Dynamic scoped alias avoids importing unrelated installed versions.
    package_alias='sst_pklsa_a003_runtime_v030'
    if package_alias in sys.modules:del sys.modules[package_alias]
    module_spec=importlib.util.spec_from_file_location(package_alias,init,submodule_search_locations=[str(init.parent)])
    if module_spec is None or module_spec.loader is None:raise RuntimeError('E010 native module cannot load')
    module=importlib.util.module_from_spec(module_spec)
    sys.modules[package_alias]=module
    try:module_spec.loader.exec_module(module)
    finally:pass
    if getattr(module,'__version__',None)!='0.3.1':raise RuntimeError('E010 version mismatch')
    native=module.Workbench.open(wb,contract=contract_file)
    resolved=[r for r in native.resolve_sources() if r.source_id==SOURCE_ID]
    if len(resolved)!=1 or resolved[0].status!='RESOLVED' or Path(resolved[0].path).resolve()!=atlas.resolve():
        raise RuntimeError('E010 native resolver did not admit exactly the A003 source')
    carriers=carrier_rows(atlas,registry)
    ledger={'schema':'sst.a003.e010-carrier-ledger/1','source_id':SOURCE_ID,'registration':'E010_NATIVE_SOURCE_CONTRACT_RUNTIME_OVERLAY',
            'carrier_count':len(carriers),'independent_empirical_carrier_count':0,
            'native_e010_qualified_carrier_index_written':False,
            'canonical_e010_source_contract_modified':False,'carrier_rows':carriers,
            'source_contract_sha256':sha256_file(source_contract),'runtime_contract_sha256':sha256_file(contract_file),
            'e010_core_sha256':sha256_file(core),'e010_init_sha256':sha256_file(init)}
    json_write(out/'E010_A003_CARRIER_LEDGER.json',ledger)
    return {'status':'PASS','reason':'E010 v0.3.1 native Workbench resolved A003 overlay and 8 SHA-pinned analytic carrier records',
           'registration_scope':'RUN_LOCAL_NATIVE_CONTRACT_NOT_COMMITTED_TO_E010',
           'source_contract_file':str(contract_file),'source_contract_sha256':sha256_file(contract_file),
           'e010_core_sha256':sha256_file(core),'carrier_count':len(carriers),
           'carrier_ledger_sha256':sha256_file(out/'E010_A003_CARRIER_LEDGER.json'),
           'canonical_committed':False,'native_carrier_index_written':False}


def c005_callable(c005,epsilon):
    corepath=c005/'fermat_ext'/'core.py'
    if not corepath.is_file():raise RuntimeError('C005 core.py missing')
    existing=sys.modules.get('fermat_ext')
    if existing is not None and not Path(existing.__file__).resolve().is_relative_to(c005.resolve()):
        raise RuntimeError('unrelated fermat_ext provider already imported')
    sys.path.insert(0,str(c005))
    mod=importlib.import_module('fermat_ext.core')
    if Path(mod.__file__).resolve()!=corepath.resolve() or getattr(mod,'PACKAGE_VERSION',None)!='0.6.1':
        raise RuntimeError('C005 native 0.6.1 code/version mismatch')
    def rhs(points):
        velocity,meta=mod.backend_biot_savart(points,points,epsilon=epsilon,
              kernel_model='rosenhead_midpoint',force_python=True,auto_build=False)
        if meta.get('backend')!='python':raise RuntimeError('requested C005 Python backend not used')
        result=np.asarray(velocity,dtype=float)
        if result.shape!=points.shape or not np.all(np.isfinite(result)):raise RuntimeError('nonfinite C005 time derivative')
        return result
    return rhs,{'source':'fermat_ext.core.backend_biot_savart','source_sha256':sha256_file(corepath),
        'kernel':'C005-0.6.1/rosenhead_midpoint','force_python':True,'epsilon_atlas_units':epsilon,
        'velocity_scale':'C005 beta0/2 (uncalibrated source-unit time)',
        'normalisation':'dimensionless_model_time_not_absolute_SST_time'}


def rk4(rhs,x0,T,nsteps,snapshot_every=0):
    x=np.array(x0,dtype=float,copy=True)
    h=T/nsteps
    snaps=[(0.0,x.copy())]
    for step in range(nsteps):
        k1=rhs(x);k2=rhs(x+h*.5*k1);k3=rhs(x+h*.5*k2);k4=rhs(x+h*k3)
        x=x+(h/6)*(k1+2*k2+2*k3+k4)
        if not np.all(np.isfinite(x)):raise RuntimeError('nonfinite RK4 state')
        if snapshot_every and (step+1)%snapshot_every==0:snaps.append(((step+1)*h,x.copy()))
    if not snaps or snaps[-1][0]!=T:snaps.append((T,x.copy()))
    return x,snaps


def curve_length(x):return float(np.sum(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)))


def nonlocal_vertex_distance(x):
    # Vertex-distance diagnostic only, NOT a segment-to-segment/reconnection certification.
    arr=np.asarray(x,dtype=float);n=len(arr)
    d=np.linalg.norm(arr[:,None,:]-arr[None,:,:],axis=2)
    ii=np.arange(n);neighbour=np.abs(ii[:,None]-ii[None,:]);neighbour=np.minimum(neighbour,n-neighbour)
    d[neighbour<=3]=np.inf
    return float(d.min())


def temporal_run(atlas,registry,c005,output,*,epsilon=0.05,final_time=2.0,levels=(150,300,600),steps=(4,8,16)):
    """Real time-stepping: dX/dt=u_epsilon[X] with C005 as RHS at EVERY RK stage."""
    levels=tuple(levels);steps=tuple(steps)
    if any(1200%n for n in levels) or sorted(levels)!=list(levels) or len(set(levels))!=len(levels):
        raise ValueError('levels must be sorted distinct divisors of the frozen N=1200 seed')
    if len(steps)!=3 or not(steps[1]==2*steps[0] and steps[2]==2*steps[1]):
        raise ValueError('timesteps must be a fixed-end-time halving ladder')
    if not (0<epsilon<100 and 0<final_time<100):raise ValueError('epsilon or final time out of range')
    rhs,provider=c005_callable(c005,epsilon)
    record=[];metrics=[];npz={};temporal_checks=[];spatial_checks=[]
    for sid in SEEDS:
        base=next(r for r in registry['records'] if r['id']==sid and r['points']==1200 and r['sampling']=='uniform_t')
        src=safe_atlas_file(atlas,base['file'])
        if sha256_file(src)!=base['sha256']:raise RuntimeError('atlas changed')
        original=read_xyz(src,1200)
        finals={}
        for n in levels:
            initial=original[::1200//n].copy()
            runsteps=steps if n!=levels[-1] else (steps[-1],)
            ends={}
            for nsteps in runsteps:
                end,snaps=rk4(rhs,initial,final_time,nsteps,snapshot_every=max(1,nsteps//4))
                ends[nsteps]=end
                event={'seed':sid,'N':n,'steps':nsteps,'dt':final_time/nsteps,'t_final':final_time,
                    'initial_length':curve_length(initial),'final_length':curve_length(end),
                    'relative_length_change':(curve_length(end)-curve_length(initial))/curve_length(initial),
                    'max_displacement':float(np.max(np.linalg.norm(end-initial,axis=1))),
                    'initial_nonlocal_vertex_distance':nonlocal_vertex_distance(initial),
                    'final_nonlocal_vertex_distance':nonlocal_vertex_distance(end),
                    'snapshots':[{'t':t,'length':curve_length(s),'nonlocal_vertex_distance':nonlocal_vertex_distance(s)} for t,s in snaps]}
                record.append(event)
                if nsteps==steps[-1]:
                    finals[n]=end
                    npz[f'{sid}_N{n}_initial']=initial
                    npz[f'{sid}_N{n}_final']=end
            if len(runsteps)==3:
                a,b,c=[ends[z] for z in steps]
                e_coarse=float(np.linalg.norm(a-b))
                e_fine=float(np.linalg.norm(b-c))
                relative=e_fine/max(float(np.linalg.norm(c-initial)),1e-15)
                order=math.log2(e_coarse/e_fine) if e_coarse>0 and e_fine>0 else None
                good=(e_fine<=max(1e-9,e_coarse*.6) and relative<1e-3)
                temporal_checks.append({'seed':sid,'N':n,'dt_steps':list(steps),
                    'coarse_to_medium_difference':e_coarse,'medium_to_fine_difference':e_fine,
                    'relative_fine_error_proxy':relative,'observed_order':order,'PASS':good})
        if len(levels)>=3:
            a,b,c=levels[-3:]
            # aligned nested meshes: every second point of a finer level is the coarser vertex.
            db=finals[b][::b//a]-finals[a]
            dc=finals[c][::c//b]-finals[b]
            errab=float(np.linalg.norm(db)/math.sqrt(len(db)))
            errbc=float(np.linalg.norm(dc)/math.sqrt(len(dc)))
            good=(errbc<max(1e-9,errab*.7))
            spatial_checks.append({'seed':sid,'levels':[a,b,c],
               'rms_12':errab,'rms_23':errbc,'PASS':good})
    npz_path=output/'G6_TEMPORAL_TRAJECTORIES.npz';np.savez_compressed(npz_path,**npz)
    all_t=all(x['PASS'] for x in temporal_checks)
    all_s=all(x['PASS'] for x in spatial_checks) if spatial_checks else False
    all_noncollision=all(x['final_nonlocal_vertex_distance']>1e-5 and
                 x['initial_nonlocal_vertex_distance']>1e-5 for x in record)
    evidence={'schema':'sst.a003.g6.temporal-finite-core/1','status': 'PASS_NUMERICAL_TRAJECTORY_NOT_EULER' if all_t and all_s and all_noncollision else 'FAIL_NUMERICAL_TRAJECTORY',
       'model':'regularized vortex filament ODE dX/dt = C005_BiotSavart(X,X); NOT continuum Euler',
       'provider':provider,'time_integrator':'classical_explicit_RK4_NEW_ORCHESTRATION_EXISTING_C005_RHS',
       'time_calibrated_to_SST':False,'physical_core_calibrated':False,'time_final':final_time,
       'timestep_ladder':list(steps),'resolution_ladder':list(levels),'temporal_checks':temporal_checks,
       'spatial_checks':spatial_checks,'vertex_distance_positive':all_noncollision,
       'trajectory_npz_sha256':sha256_file(npz_path),'trajectory_samples':record,
       'note':'No filament remeshing, viscous core evolution, pressure-Poisson solver, Euler closure, exact segment proximity proof, or independent topology certificate.'}
    json_write(output/'G6_TEMPORAL_DIAGNOSTICS.json',evidence)
    return evidence


def report_pdf(folder,summary,ledger):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
        from reportlab.pdfgen import canvas
    except ImportError:return {'status':'UNRESOLVED_REPORTLAB_UNAVAILABLE'}
    path=folder/'A003_v0.3.0_G6_TEMPORAL_REPORT.pdf';c=canvas.Canvas(str(path),pagesize=A4)
    w,h=A4;c.setFillColor(HexColor('#14263B'));c.rect(0,h-112,w,112,fill=1,stroke=0)
    c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',17)
    c.drawString(42,h-52,'A003 v0.3.0 - PKLSA / RK4')
    c.setFont('Helvetica',10);c.drawString(42,h-74,'Finite-core temporal diagnostics / Framework v1.0.10')
    c.setFillColor(HexColor('#101A28'));c.setFont('Helvetica',9)
    lines=[f"Run: {summary['run_id']}",f"G5: {summary['g5']['status']}",
        f"E010 source registration: {summary['e010_registration']['status']}",
        f"C005 + RK4 trajectory: {summary['temporal']['status']}",
        f"G6 physics: {summary['overall_g6_status']}",
        f"Framework reported status: {summary['framework']['release_status']}",
        '', 'GateLedger:']
    lines += [f"{z['gate_id']}: {z['status']} / {z['qualification']} / {z['execution_status']}" for z in ledger['records']]
    lines += ['', 'Scientific boundary:', 'E010 native source resolver + run-local provenance; not canonical E010 registry write.',
              'Actual RK4 filament evolution uses the existing C005 v0.6.1 finite-core RHS.',
              'No physical core calibration / incompressible Euler time closure.',
              'PASS of numerical checks is diagnostic only; G6 is UNRESOLVED.']
    y=h-142
    for line in lines:
        if y<65:c.showPage();c.setFont('Helvetica',9);y=h-55
        c.drawString(42,y,line[:113]);y-=18
    c.save();return {'status':'PASS','path':path.name,'sha256':sha256_file(path)}


def main(argv=None):
    p=argparse.ArgumentParser(description='A003 v0.3.0 E010 registered analytic carriers + native C005 finite-core temporal RK4')
    p.add_argument('--atlas',type=Path);p.add_argument('--workbench',type=Path);p.add_argument('--framework-root',type=Path)
    p.add_argument('--e010-root',type=Path);p.add_argument('--c005-root',type=Path);p.add_argument('--g5-summary',type=Path)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'A003_Fourier_Knot_Import_Adapter_v0.3.0-outputs')
    p.add_argument('--epsilon',type=float,default=0.05);p.add_argument('--final-time',type=float,default=2.0)
    p.add_argument('--full',action='store_true',help='extra N=1200 trajectory level (costly), without overriding the certified 3-level checks')
    p.add_argument('--preflight-only',action='store_true')
    args=p.parse_args(argv)
    atlas=args.atlas.resolve() if args.atlas else resolve_atlas_root(None)
    wb=find_workbench(atlas,args.workbench)
    fw,meta,mod,fw_hash=load_framework(args.framework_root or (wb/FRAMEWORK_REL if wb else None))
    registry,geometry=source_check(atlas)
    g5=g5_check(find_g5_summary(atlas,args.g5_summary,wb))
    # v1.0.10 policy: an intact scientific G5 FAIL does NOT stop downstream diagnostics.
    # A tampered G5 GateLedger does stop: never reclassify an integrity failure as science.
    if g5['status']=='FAIL':
        gp=Path(g5.get('file',''))
        lp=gp.parent/'GATE_LEDGER.json'
        if not gp.is_file() or not lp.is_file():
            raise RuntimeError('G5 failed without complete signed receipt; abort integrity preflight')
        ld=json.loads(lp.read_text(encoding='utf-8'))
        raw={k:v for k,v in ld.items() if k!='ledger_sha256'}
        digest=hashlib.sha256((json.dumps(raw,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')).hexdigest()
        if digest!=ld.get('ledger_sha256'):
            raise RuntimeError('G5 ledger SHA256 mismatch; integrity abort')
        g5['scientific_fail_diagnostics_allowed']=True
    e010=args.e010_root.resolve() if args.e010_root else (wb/E010_REL if wb else None)
    c005=args.c005_root.resolve() if args.c005_root else (wb/C005_REL if wb else None)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    output=args.out.expanduser().resolve()/run_id;output.mkdir(parents=True,exist_ok=False)
    if args.preflight_only:registration={'status':'UNRESOLVED','reason':'preflight only, native import not performed'}
    else:registration=register_e010(atlas,registry,wb,e010,output)
    if args.preflight_only or c005 is None or not (c005/'fermat_ext'/'core.py').is_file():
        temporal={'status':'UNRESOLVED','reason':'C005 unavailable or preflight-only'}
    else:
        temporal=temporal_run(atlas,registry,c005,output,epsilon=args.epsilon,final_time=args.final_time)
        if args.full:
            # Extra high-resolution spatial demonstration, separately from the bounded certified ladder.
            # Avoid pretending a single high-res run is convergence evidence.
            rhs,prov=c005_callable(c005,args.epsilon)
            rows={}
            for sid in SEEDS:
                record=next(z for z in registry['records'] if z['id']==sid and z['points']==1200 and z['sampling']=='uniform_t')
                x=read_xyz(safe_atlas_file(atlas,record['file']),1200)
                y,_=rk4(rhs,x,args.final_time,16)
                rows[sid]={'N':1200,'steps':16,'max_displacement':float(np.max(np.linalg.norm(y-x,axis=1))),
                          'relative_length_change':(curve_length(y)-curve_length(x))/curve_length(x)}
            json_write(output/'G6_FULL_N1200_DIAGNOSTIC.json',{'status':'DIAGNOSTIC_ONLY','results':rows})
    from_framework=mod.GateDefinition
    definitions=[from_framework('G6P0','Framework v1.0.10 exact SHA and local canonical status'),
       from_framework('G6P1','A003 source manifest plus intact measured corrected G5 receipt',('G6P0',)),
       from_framework('G6P2','Real E010 v0.3.1 source resolver available',('G6P1',)),
       from_framework('G6P3','C005 v0.6.1 kernel invoked for time-stepping',('G6P1',)),
       from_framework('G6P4','C005 source-unit temporal field and spatial convergence',('G6P3',)),
       from_framework('G6P5','Trajectory finite-value and local noncollision vertex diagnostics',('G6P3',)),
       from_framework('G6P6','E010 native runtime source contract + eight hashed analytic carrier records',('G6P2',)),
       from_framework('G6P7','Actual C005-RHS/RK4 timestep-halving and spatial trajectory convergence',('G6P3','G6P6')),
       from_framework('G6P8','Canonical E010 carrier registry commit and independent source admission',('G6P6',)),
       from_framework('G6P9','Continuum Euler evolution, physical finite-core calibration and topology preservation',('G6P7',)),
       from_framework('G6','Scientific source-native Euler/PKLSA dynamical qualification',('G6P1','G6P6','G6P7','G6P8','G6P9'))]
    ledger=mod.GateLedger(definitions,strict_dependencies=False)
    def res(status,reason,metrics=None):return {'status':status,'reason':reason,'metrics':metrics or {}}
    have_time=temporal.get('status','').startswith('PASS')
    have_failed=temporal.get('status','').startswith('FAIL')
    ev={
      'G6P0':lambda:res('PASS' if meta.get('status')=='CANONICAL_FROZEN' else 'UNRESOLVED',
               'Pinned gate SHA checked; freeze status read from local RELEASE_INFO.json',{'sha256':fw_hash,'status':meta.get('status')}),
      'G6P1':lambda:res(g5['status'],'Frozen manifest validated and original corrected G5 evidence verified',g5),
      'G6P2':lambda:res(registration['status'],'E010 resolver loaded and run-local source overlay validated',registration),
      'G6P3':lambda:res('PASS' if have_time or have_failed else 'UNRESOLVED','Actual existing C005 v0.6.1 evaluated as RK4 RHS',temporal.get('provider')),
      'G6P4':lambda:res('UNRESOLVED' if not (have_time or have_failed) else
            ('PASS' if all(x['PASS'] for x in temporal['spatial_checks']) else 'FAIL'),
               'Nested spatial trajectory convergence, same fixed time and 16 RK4 steps'),
      'G6P5':lambda:res('UNRESOLVED' if not (have_time or have_failed) else
            ('PASS' if temporal['vertex_distance_positive'] else 'FAIL'),
               'Numerical nonlocal vertex distances only; NOT segment-intersection guarantee'),
      'G6P6':lambda:res(registration['status'],'E010 native source contract resolution; not persisted E010 carrier index',registration),
      'G6P7':lambda:res('UNRESOLVED' if not (have_time or have_failed) else
             ('PASS' if have_time else 'FAIL'),'RK4 timestamped X(t) plus fixed-final-time halving residuals',
             {'temporal_checks':temporal.get('temporal_checks'),'spatial_checks':temporal.get('spatial_checks')}),
      'G6P8':lambda:res('UNRESOLVED','No write to E010 canonical source/registry; runtime overlay only'),
      'G6P9':lambda:res('UNRESOLVED','Regularized filament RK4 not a source-native incompressible Euler/pressure-Poisson closure'),
      'G6':lambda:res('UNRESOLVED','Physical Euler closure and canonical E010 registry unresolved; diagnostic progress only')
    }
    ledger.run_evaluators(ev);l=ledger.to_dict();ledger.write(output/'GATE_LEDGER.json')
    summary={'schema':SCHEMA,'run_id':run_id,'adapter_version':VERSION,'overall_g6_status':'UNRESOLVED',
        'physical_euler_certified':False,'e010_canonical_modified':False,'framework':{'version':'1.0.10','release_status':meta.get('status'),'gates_sha256':fw_hash},
        'atlas_manifest_sha256':EXPECTED_MANIFEST,'g5':g5,'e010_registration':registration,
        'temporal':{k:v for k,v in temporal.items() if k not in ('trajectory_samples',)},
        'scientific_scope':'RK4 regularized vortex filament model, not continuum Euler',
        'gate_statuses':{x['gate_id']:x['status'] for x in l['records']},
        'failed_gates':[x['gate_id'] for x in l['records'] if x['status']=='FAIL'],
        'unresolved_gates':[x['gate_id'] for x in l['records'] if x['status']=='UNRESOLVED'],
        'gate_ledger_sha256':sha256_file(output/'GATE_LEDGER.json')}
    json_write(output/'G6_TEMPORAL_SUMMARY.json',summary)
    pdf=report_pdf(output,summary,l);json_write(output/'PDF_RENDER.json',pdf)
    print(json.dumps({'output':str(output),'g5':g5['status'],'g6':summary['overall_g6_status'],
         'registration':registration['status'],'temporal':temporal['status'],'gates':summary['gate_statuses'],'pdf':pdf['status']},indent=2))
    return 2 if summary['failed_gates'] else 3

if __name__=='__main__':raise SystemExit(main())
