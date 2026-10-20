#!/usr/bin/env python3
"""A003 v0.2.9: source-native PKLSA/E010 + C005 G6 readiness and field diagnostics.

Deliberately NOT an Euler time integrator: a finite-core instantaneous field / Jacobian
cannot qualify G6. G6 stays UNRESOLVED until independent temporal solver evidence exists.
Gates execute independently using exact pinned framework 1.0.10 GateLedger.
"""
from __future__ import annotations
import argparse, hashlib, importlib, json, os, secrets, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from a003_diagnostic_v027 import load_framework, json_write
from fourier_atlas_adapter import resolve_atlas_root, validate_atlas, read_xyz, sha256_file, safe_atlas_file

SEEDS=('fibonacci_torus_F3','fibonacci_torus_F4')
NS=(1200,2400,4800)
SCHEMA='sst.a003.pklsa-g6-readiness/1'
EXPECTED_MANIFEST='01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d'
E010_REL=Path('01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1')
C005_REL=Path('01_research/C_dynamics/C005_fermat_biot_savart/C005-v0.6.1')
FRAMEWORK_REL=Path('06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.10')


def find_workbench(atlas:Path,explicit:Path|None):
    if explicit: return explicit.expanduser().resolve()
    env=os.getenv('SST_WORKBENCH_ROOT')
    if env:return Path(env).expanduser().resolve()
    for base in [atlas,*atlas.parents]:
        if (base/'06_templates'/'SST_Falsifier_Framework').is_dir() and (base/'01_research').is_dir():
            return base
    return None


def find_g5_summary(atlas:Path, explicit:Path|None, workbench:Path|None):
    if explicit:return explicit.resolve()
    # Look at the preceding release's immutable run folders, never synthesize observations.
    parent=atlas.parent
    dirs=[parent/'A003_Fourier_Knot_Import_Adapter_v0.3.0-outputs',
          parent/'A003_Fourier_Knot_Import_Adapter_v0.2.9-outputs',
          parent/'A003_Fourier_Knot_Import_Adapter_v0.2.8.1-outputs',
          parent/'A003_Fourier_Knot_Import_Adapter_v0.2.8.1'/'outputs']
    items=[]
    for d in dirs:
        if d.is_dir():items.extend(d.glob('*/QUALIFICATION_SUMMARY.json'))
    return sorted(items,key=lambda p:p.stat().st_mtime)[-1] if items else None


def source_check(atlas:Path):
    registry,report=validate_atlas(atlas)
    actual=registry.get('atlas_manifest_sha256')
    if actual!=EXPECTED_MANIFEST:raise RuntimeError('A003 manifest SHA256 differs from frozen v0.1.2 baseline')
    for sid in SEEDS:
        for n in NS:
            rows=[x for x in registry['records'] if x['id']==sid and x['points']==n and x['sampling']=='uniform_t']
            if len(rows)!=1:raise RuntimeError(f'missing or duplicated {sid}/{n}')
    return registry,report


def g5_check(path:Path|None):
    if path is None or not path.is_file():
        return {'status':'UNRESOLVED','reason':'No measured v0.2.8.1 G5 summary supplied/found'}
    d=json.loads(path.read_text('utf-8'))
    core_ok=(d.get('adapter_version') in ('0.2.8.1','0.2.9','0.3.0') and
        d.get('corrected_g5_bounded_result')=='PASS_INVARIANT_SCREEN_NOT_CERTIFIED' and
        d.get('measured_provider_observations')==32 and
        d.get('source_manifest_sha256')==EXPECTED_MANIFEST and
        d.get('exit_code')==0 and not d.get('failed_gates'))
    lp=path.parent/'GATE_LEDGER.json'
    pp=path.parent/'g5_corrected_four_resolutions.json'
    if not lp.is_file() or not pp.is_file():
        return {'status':'UNRESOLVED','reason':'Paired GATE_LEDGER.json / provider raw observations absent',
                'summary':str(path),'sha256':sha256_file(path)}
    led=json.loads(lp.read_text('utf-8'))
    raw={k:v for k,v in led.items() if k!='ledger_sha256'}
    canon=(json.dumps(raw,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    digest=hashlib.sha256(canon).hexdigest()
    gates={x['gate_id']:x for x in led.get('records',[])}
    expected={'G0','G1','G5Q0','G5Q1','G5Q2','G5Q3','G5Q4','G5Q5','G5Q6','G5Q7'}
    ledger_ok=(digest==led.get('ledger_sha256') and all(gates.get(q,{}).get('status')=='PASS' for q in expected))
    observations=json.loads(pp.read_text('utf-8'))
    obs_ok=(observations.get('expected_cases')==32 and observations.get('observation',{}).get('provider')=='pyknotid')
    return {'status':'PASS' if core_ok and ledger_ok and obs_ok else 'FAIL',
            'reason':'Measured bounded G5 with intact ledger and raw provider evidence; not knot certification',
            'file':str(path),'sha256':sha256_file(path),'ledger_sha256':sha256_file(lp),
            'raw_provider_sha256':sha256_file(pp), 'run_id':d.get('run_id'),
            'historical_stock_fail_preserved':d.get('baseline_historical_stock_fail_preserved')}


def provider_check(root:Path|None,name:str, rel:Path, marker:Path):
    p=(root/rel if root else None)
    if not p or not (p/marker).is_file():
        return {'status':'UNRESOLVED','path':str(p) if p else None,'reason':f'{name} source not installed at canonical relative path'}
    return {'status':'PASS','path':str(p),'marker':str(marker),'marker_sha256':sha256_file(p/marker),
            'authority':'LOCAL_SOURCE_PRESENT_NOT_VALIDATED_FOR_A003'}


def finite_core_field(atlas:Path, registry:dict, c005:Path, *, epsilon=0.05, backend_function=None):
    """Use C005 v0.6.1 directly, no copied kernels or synthetic velocity evidence."""
    if backend_function is None:
        core_path=c005/'fermat_ext'/'core.py'
        if not core_path.is_file():raise FileNotFoundError('C005 core.py absent')
        # Do not allow an unrelated fermat_ext from site-packages.
        existing=sys.modules.get('fermat_ext')
        if existing is not None and not Path(existing.__file__).resolve().is_relative_to(c005.resolve()):
            raise RuntimeError('Unrelated fermat_ext already loaded')
        sys.path.insert(0,str(c005))
        core=importlib.import_module('fermat_ext.core')
        if Path(core.__file__).resolve()!=core_path.resolve() or getattr(core,'PACKAGE_VERSION',None)!='0.6.1':
            raise RuntimeError('C005 0.6.1 API/source identity mismatch')
        def backend_function(points,probes):
            return core.backend_biot_savart_with_jacobian(points,probes,
                epsilon=epsilon,kernel_model='rosenhead_midpoint',force_python=True,auto_build=False)
    results={}; diagnostics=[]
    for sid in SEEDS:
        field_levels={}
        for n in NS:
            record=next(x for x in registry['records'] if x['id']==sid and x['points']==n and x['sampling']=='uniform_t')
            src=safe_atlas_file(atlas,record['file'])
            if sha256_file(src)!=record['sha256']:raise RuntimeError('source SHA changed during G6')
            p=read_xyz(src,n)
            ctr=p.mean(axis=0)
            radius=float(np.max(np.linalg.norm(p-ctr,axis=1)))
            dirs=np.array([[0.15,0.2,0.33],[0.31,0.17,-0.2],[-0.23,0.18,0.15],
                [0.08,-0.29,0.25],[0.27,0.22,0.19],[-0.16,-0.13,-0.28]],dtype=float)
            # A fixed probe family per source, recomputed from N=1200 only below; compute
            # its reference geometry independently to avoid N-dependent probe positions.
            rec0=next(x for x in registry['records'] if x['id']==sid and x['points']==1200 and x['sampling']=='uniform_t')
            base=read_xyz(safe_atlas_file(atlas,rec0['file']),1200)
            bc=base.mean(axis=0);br=float(np.max(np.linalg.norm(base-bc,axis=1)))
            probes=bc+br*dirs
            field,jac,meta=backend_function(p,probes)
            f=np.asarray(field,dtype=float); j=np.asarray(jac,dtype=float)
            if f.shape!=(len(dirs),3) or j.shape!=(len(dirs),3,3) or not np.all(np.isfinite(f)) or not np.all(np.isfinite(j)):
                raise RuntimeError('C005 returned nonfinite or invalid field/Jacobian data')
            rel_div=float(np.max(np.abs(np.trace(j,axis1=1,axis2=2)))/max(np.max(np.linalg.norm(j,axis=(1,2))),1e-15))
            field_levels[n]=f
            diagnostics.append({'id':sid,'N':n,'provider':'C005-v0.6.1/fermat_ext.core',
                 'epsilon_atlas_units_assumed':epsilon,'source_xyz_sha256':sha256_file(src),
                 'backend':meta,'field_l2':float(np.linalg.norm(f)),
                 'relative_divergence':rel_div,'finite':True})
        rel12=float(np.linalg.norm(field_levels[2400]-field_levels[1200])/max(np.linalg.norm(field_levels[2400]),1e-15))
        rel23=float(np.linalg.norm(field_levels[4800]-field_levels[2400])/max(np.linalg.norm(field_levels[4800]),1e-15))
        results[sid]={'relative_change_1200_2400':rel12,'relative_change_2400_4800':rel23,
                     'converging':rel23<max(rel12*1.25,1e-10) and rel23<0.02}
    return {'schema':'sst.a003.g6.c005-velocity-probe/1','kernel':'C005_v0.6.1_rosenhead_midpoint',
       'epsilon_atlas_units_assumed':epsilon,'physical_core_calibrated':False,
       'euler_time_integrated':False,'results':results,'samples':diagnostics,
       'claim_boundary':'Instantaneous velocity/Jacobian only; no Euler time integration, no vortex stability proof'}


def report_pdf(out:Path,summary:dict,ledger:dict):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen.canvas import Canvas
    except ImportError:return {'status':'UNRESOLVED_NO_REPORTLAB'}
    dst=out/'A003_G6_PKLSA_DIAGNOSTIC_REPORT.pdf'
    pdf=Canvas(str(dst),pagesize=A4); w,h=A4
    pdf.setFont('Helvetica-Bold',14);pdf.drawString(44,h-55,'A003 v0.2.9 - PKLSA / C005 G6 Diagnostic')
    pdf.setFont('Helvetica',9)
    lines=[f"Run: {summary['run_id']}",f"Overall G6: {summary['overall_g6_status']}",
           f"Framework: {summary['framework']['version']} / {summary['framework']['source_status']}",
           f"G5 baseline: {summary['g5']['status']}",
           'Finite-core probe uses existing C005 v0.6.1 (if installed).',
           'E010 PKLSA supplies source/geometry, NOT an Euler integrator.',
           'No time integration has been executed; G6 cannot be certified.', '', 'Gate results:']
    for x in ledger.get('records',[]):
        lines.append(f"{x['gate_id']}: {x['status']} / {x['qualification']} / {x['execution_status']}")
    y=h-90
    for line in lines:
        pdf.drawString(44,y,line[:111]);y-=17
        if y<55:pdf.showPage();pdf.setFont('Helvetica',9);y=h-60
    pdf.save();return {'status':'PASS','file':dst.name,'sha256':sha256_file(dst)}


def main(argv=None):
    parser=argparse.ArgumentParser(description='G6 source-native PKLSA/E010 and C005 finite-core readiness, fail-closed')
    parser.add_argument('--atlas',type=Path)
    parser.add_argument('--workbench',type=Path)
    parser.add_argument('--framework-root',type=Path)
    parser.add_argument('--e010-root',type=Path)
    parser.add_argument('--c005-root',type=Path)
    parser.add_argument('--g5-summary',type=Path)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parent.parent/'A003_Fourier_Knot_Import_Adapter_v0.2.9-outputs')
    parser.add_argument('--epsilon',type=float,default=0.05)
    parser.add_argument('--preflight-only',action='store_true')
    args=parser.parse_args(argv)
    if not (0<args.epsilon<100):parser.error('epsilon must be positive and finite-ish in source-coordinate units')
    atlas=args.atlas.resolve() if args.atlas else resolve_atlas_root(None)
    wb=find_workbench(atlas,args.workbench)
    fw,fw_meta,mod,fw_sha=load_framework(args.framework_root or (wb/FRAMEWORK_REL if wb else None))
    registry,geometry=source_check(atlas)
    g5=g5_check(find_g5_summary(atlas,args.g5_summary,wb))
    e010_root=args.e010_root or (wb/E010_REL if wb else None)
    c005_root=args.c005_root or (wb/C005_REL if wb else None)
    e010=provider_check(wb,'E010 v0.3.1',E010_REL,Path('sst_pklsa/__init__.py')) if args.e010_root is None else provider_check(args.e010_root.parent,'E010 v0.3.1',Path(args.e010_root.name),Path('sst_pklsa/__init__.py'))
    c005=provider_check(wb,'C005 v0.6.1',C005_REL,Path('fermat_ext/core.py')) if args.c005_root is None else provider_check(args.c005_root.parent,'C005 v0.6.1',Path(args.c005_root.name),Path('fermat_ext/core.py'))
    time_integrator={'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
      'reason':'No registered source-native Euler/RK4 temporal trajectory provider for these A003 curves was verified in E010 or C005 v0.6.1'}
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')+'_'+secrets.token_hex(5)
    output=args.out.expanduser().resolve()/run_id
    output.mkdir(parents=True,exist_ok=False)
    cache={}
    def field():
        if 'field' not in cache:
            if args.preflight_only or c005['status']!='PASS':
                cache['field']=None
            else:
                cache['field']=finite_core_field(atlas,registry,c005_root,epsilon=args.epsilon)
            json_write(output/'G6_FINITE_CORE_PROBE.json',cache['field'] if cache['field'] is not None else
                    {'status':'NOT_EXECUTED','reason':'C005 unavailable or preflight-only'})
        return cache['field']
    D=mod.GateDefinition
    ledger=mod.GateLedger([
        D('G6P0','Framework 1.0.10 exact pinned source and claimed freeze metadata'),
        D('G6P1','A003 v0.1.2 source, XYZ integrity and qualified bounded G5 receipt',('G6P0',)),
        D('G6P2','E010 source-native PKLSA geometry provider present',('G6P1',)),
        D('G6P3','C005 source-native instantaneous finite-core kernel execution',('G6P1',)),
        D('G6P4','C005 field convergence 1200/2400/4800 on A003 F3/F4',('G6P3',)),
        D('G6P5','C005 analytic Jacobian has low divergence',('G6P3',)),
        D('G6P6','E010 native A003 carrier/lineage admission',('G6P2',)),
        D('G6P7','Source-native coupled Euler temporal integration and timestep convergence',('G6P3','G6P6')),
        D('G6','Scientific PKLSA/Euler dynamical qualification',('G6P1','G6P4','G6P5','G6P6','G6P7')),
    ])
    def result(status,reason,metrics=None):return {'status':status,'reason':reason,'metrics':metrics or {}}
    evaluator={
      'G6P0':lambda:result('PASS' if fw_meta.get('status')=='CANONICAL_FROZEN' else 'UNRESOLVED',
                         'Exact framework source hash pinned; canonical status requires local release metadata',
                         {'sha256':fw_sha,'release_status':fw_meta.get('status')}),
      'G6P1':lambda:result(g5['status'],'Atlas SHA qualified; previous measured bounded G5 required',{'g5':g5}),
      'G6P2':lambda:result(e010['status'],'E010 static geometry provider source inspection',e010),
      'G6P3':lambda:result('UNRESOLVED' if field() is None else 'PASS',
                         'C005 spatial velocity/Jacobian; instantaneous diagnostic only',
                         {'kernel_present':field() is not None,'samples':len(field()['samples']) if field() else 0}),
      'G6P4':lambda:result('UNRESOLVED' if field() is None else
                         ('PASS' if all(r['converging'] for r in field()['results'].values()) else 'FAIL'),
                         'Source geometry ladder relative field change',field()['results'] if field() else {}),
      'G6P5':lambda:result('UNRESOLVED' if field() is None else
                         ('PASS' if max(q['relative_divergence'] for q in field()['samples'])<1e-8 else 'FAIL'),
                         'Divergence of regularized field only; not time-resolved Euler incompressibility',
                         {'max_relative_divergence':max(q['relative_divergence'] for q in field()['samples']) if field() else None}),
      'G6':lambda:result('UNRESOLVED','No source-native Euler time integration + temporal convergence; physics unresolved'),
    }
    # Source/manifest integrity failure aborts before running, scientific negative gates do not stop execution.
    ledger.run_evaluators(evaluator)
    actual=ledger.to_dict();ledger.write(output/'GATE_LEDGER.json')
    summ={'schema':SCHEMA,'run_id':run_id,'overall_g6_status':'UNRESOLVED',
          'scientific_qualification':'NOT_CERTIFIED','g6_pklsa_euler_run':False,
          'framework':{'version':fw_meta.get('version'),'source_status':fw_meta.get('status'),
                       'gates_sha256':fw_sha,'integration':'GateLedger, NOT full blind instance'},
          'atlas':{'version':'v0.1.2','manifest_sha256':EXPECTED_MANIFEST},
          'g5':g5,'e010':e010,'c005':c005,
          'source_lineage_verified':False,'pklsa_time_integrator_verified':False,
          'missing_time_provider':time_integrator,
          'completed_scientific_evaluators':sum(r['execution_status']=='EXECUTED' for r in actual['records']),
          'failed_gates':[r['gate_id'] for r in actual['records'] if r['status']=='FAIL'],
          'unresolved_gates':[r['gate_id'] for r in actual['records'] if r['status']=='UNRESOLVED'],
          'outcome':'G5_BOUNDED_COMPLETED_G6_DIAGNOSTIC_ONLY',
          'reason':'Static finite-core kernel cannot replace trajectory-resolved Euler/PKLSA closure'}
    json_write(output/'G6_READINESS_SUMMARY.json',summ)
    pdf=report_pdf(output,summ,actual)
    json_write(output/'PDF_RENDER.json',pdf)
    print(json.dumps({'run_dir':str(output),'g6':summ['overall_g6_status'],
           'gate_statuses':{r['gate_id']:r['status'] for r in actual['records']},'pdf':pdf['status']},indent=2))
    # 3 = unresolved, distinct from scientific FAIL (2), true infrastructure defects raise normally.
    return 2 if summ['failed_gates'] else 3

if __name__=='__main__':
    raise SystemExit(main())
