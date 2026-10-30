from __future__ import annotations
from pathlib import Path
import json,os,sys
from runtime_options import parse
ROOT=Path(__file__).resolve().parent

def _run_preview_with_heartbeat(ROOT,overrides):
    from experiment.science import run_suite,run_matrix
    if overrides.get('domain_study_only'):
        from experiment.science import _resolve
        from experiment.domain import run_domain_study
        domain=run_domain_study(ROOT,'PREVIEW',ROOT/'A075_Hydrodynamische_Resonante_Invanging_v0.2.4-outputs'/'science'/'domain_study',_resolve('PREVIEW',overrides))
        result={'physical_answer':'UNRESOLVED','cases':{},'backends':{},'domain_study':domain}
    else:
        result=run_matrix(ROOT,'PREVIEW',ROOT/'A075_Hydrodynamische_Resonante_Invanging_v0.2.4-outputs'/'science',overrides) if overrides.get('backends') else run_suite(ROOT,'PREVIEW',overrides=overrides)
    print(json.dumps({'mode':'PREVIEW','physical_answer':result['physical_answer'],
                      'cases':{k:v['status'] for k,v in result.get('cases',{}).items()},
                      'backends':{k:v['status'] for k,v in result.get('backends',{}).items()},'domain_study_executed':result.get('domain_study',{}).get('executed',False)},indent=2))
    return

if __name__=='__main__':
    args,overrides,plan=parse(sys.argv[1:])
    if args.plan:
        from experiment.science import probe_backend
        probe={x:probe_backend(x,ROOT) for x in overrides.get('backends',[])}
        print(json.dumps({'mode':args.mode,'plan':plan,'backend_preflight':probe,
                          'status':'PLAN_ONLY_NOT_EXECUTED'},indent=2))
        raise SystemExit(0)
    if args.mode=='STATUS':
        from experiment.heartbeat import status
        print(json.dumps(status(ROOT),indent=2,sort_keys=True))
        raise SystemExit(0)
    if args.mode=='GPU_PROBE':
        from framework_bootstrap import load_framework
        framework=load_framework()
        from sst_falsifier.sycl_worker import probe_worker
        from tools.gpu_probe import stage_template_worker
        from experiment.science import save, _resolve
        stage=stage_template_worker(framework,ROOT)
        probe=probe_worker(ROOT) if stage.get('success') else {'available':False,'error':stage.get('reason')}
        from experiment.science import probe_backend
        xpu=probe_backend('gpu',ROOT)
        evidence={'schema':'A075-MULTI-GPU-DEVICE-PROBE-2','framework_version':'1.1.0',
            'template_source_staging':stage,'probe':probe,'pytorch_xpu_euler_probe':xpu,'gpu_euler_backend_certified':False,
            'qualification':'DEVICE_DIAGNOSTIC_ONLY','sycl_worker_is_gpu':bool(probe.get('is_gpu',False)),
            'reason':'Framework SYCL worker computes Biot-Savart, not the A075 FFT/Leray/RK4 Euler solver'}
        save(ROOT/'diagnostics'/'arc_device_probe.json',evidence)
        print(json.dumps(evidence,indent=2))
        raise SystemExit(0 if xpu.get('available') and probe.get('available') and probe.get('is_gpu') else 2)
    if args.mode=='RUBAN_DEPOSITION':
        from experiment.ruban_deposition import run_deposition,package_outputs
        from experiment import heartbeat
        import datetime,secrets
        def scan(text,cast):
            vals=[cast(v.strip()) for v in text.split(',') if v.strip()]
            if not vals:raise ValueError('Empty deposition scan')
            return vals
        tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
        output=ROOT/'A075_Hydrodynamische_Resonante_Invanging_v0.2.9-outputs'/tag
        heartbeat.start(ROOT,'RUBAN_DEPOSITION',args.heartbeat_seconds)
        exit_code=1
        try:
            result=run_deposition(ROOT,output,grids=scan(args.deposition_grids,int),
                sigmas=scan(args.deposition_sigmas,float),boxes=scan(args.deposition_boxes,float),
                threads=args.threads,allow_expensive=args.allow_expensive,
                track=args.deposition_track,track_T=args.track_t_end,track_dt=args.track_dt)
            import shutil
            latest_report=ROOT.parent/'A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf'
            shutil.copy2(output/'A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf',latest_report)
            packaged=package_outputs(ROOT,ROOT/'A075_Hydrodynamische_Resonante_Invanging_v0.2.9-outputs')
            print(json.dumps({'mode':'RUBAN_DEPOSITION','output':str(output),
                'cases':result['cases'],'archive':packaged,
                'framework_gates':'NOT_EXECUTED','physical_answer':'UNRESOLVED'},indent=2))
            exit_code=0
        except BaseException as exc:
            heartbeat.phase('error',message=str(exc))
            raise
        finally:heartbeat.finish(exit_code)
        raise SystemExit(exit_code)
    if args.mode=='RUBAN_FILAMENT':
        from experiment.ruban_filament import run_filament_study
        from experiment import heartbeat
        import datetime,secrets
        tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
        dest=ROOT/'ruban_filament_diagnostics'/tag
        heartbeat.start(ROOT,'RUBAN_FILAMENT',args.heartbeat_seconds)
        exit_code=1
        try:
            r=run_filament_study(ROOT,dest,n=args.filament_points,
                 T=args.filament_t_end,dt=args.filament_dt)
            print(json.dumps({'output':str(dest),'filament_diagnostic':r,'framework_gates':'NOT_EXECUTED'},indent=2))
            exit_code=0
        finally:heartbeat.finish(exit_code)
        raise SystemExit(exit_code)
    if args.mode=='RUBAN_PREVIEW':
        from experiment.ruban_study import run_ruban_study
        from experiment.science import save, _resolve
        from experiment import heartbeat
        import datetime, secrets
        tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
        dest=ROOT/'ruban_diagnostics'/tag
        heartbeat.start(ROOT,'RUBAN_PREVIEW',args.heartbeat_seconds)
        exit_code=1
        try:
            # Intentionally light, no frozen framework gates claimed.
            options=_resolve('PREVIEW',overrides)
            result=run_ruban_study(ROOT,dest,options,light=False)
            print(json.dumps({'mode':'RUBAN_PREVIEW','out':str(dest),
                'geometry_fidelity':result['geometry']['geometric_fidelity_pass'],
                'physical_answer':result['physical_answer'],'framework_gates':'NOT_EXECUTED'},indent=2))
            exit_code=0
        except BaseException as exc:
            heartbeat.phase('error',message=str(exc))
            raise
        finally:heartbeat.finish(exit_code)
        raise SystemExit(exit_code)
    if args.mode=='PREVIEW':
        from experiment import heartbeat
        heartbeat.start(ROOT,'PREVIEW',args.heartbeat_seconds)
        try:
            _run_preview_with_heartbeat(ROOT,overrides)
        except BaseException as exc:
            heartbeat.finish(1,type(exc).__name__+': '+str(exc))
            raise
        heartbeat.finish(0)
        raise SystemExit(0)
    if overrides.get('domain_study_only'):
        # Optional, explicitly non-framework-qualifying diagnostic.  Avoid a
        # misleading 2-of-3 failure and preserve all frozen run artifacts.
        from datetime import datetime,timezone
        import secrets
        from experiment import heartbeat
        from experiment.science import _resolve,save
        from experiment.domain import run_domain_study
        tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
        destination=ROOT/f'A075_Hydrodynamische_Resonante_Invanging_v0.2.9-domain-diagnostics' / tag
        heartbeat.start(ROOT,'DOMAIN_ONLY_DIAGNOSTIC',args.heartbeat_seconds)
        exit_code=1
        try:
            result=run_domain_study(ROOT,args.mode,destination,_resolve(args.mode,overrides))
            save(destination/'DOMAIN_ONLY_STATUS.json',{
                'schema':'A075-DOMAIN-ONLY-DIAGNOSTIC-1','framework_gate_qualified':False,
                'periodic_images_still_present':True,
                'mode':args.mode,'run_id':tag,'executed':result.get('executed',False),
                'status':'DIAGNOSTIC_ONLY_NOT_FREE_SPACE'})
            print(json.dumps({'mode':'DOMAIN_ONLY_DIAGNOSTIC',
                'output':str(destination),'executed':result.get('executed',False),
                'framework_gates':'NOT_EXECUTED', 'physical_answer':'UNRESOLVED'},indent=2))
            exit_code=0 if result.get('executed') else 4
        finally:
            heartbeat.finish(exit_code)
        raise SystemExit(exit_code)
    # Bound OpenMP to the same explicitly requested CPU worker count.
    os.environ['OMP_NUM_THREADS']=str(args.threads)
    os.environ['OMP_DYNAMIC']='FALSE'
    # This environment is transmitted only to the Framework's actual science adapter.
    # All scientific choices are written in A075_GATES.json and BACKEND_MANIFEST.json.
    os.environ['A075_RUNTIME_OPTIONS_JSON']=json.dumps(overrides,sort_keys=True)
    from experiment import heartbeat
    heartbeat.start(ROOT,args.mode,args.heartbeat_seconds)
    exit_code=1
    try:
        heartbeat.phase('framework_bootstrap',message='Loading immutable Framework v1.1.0 snapshot')
        from framework_bootstrap import load_framework
        load_framework()
        from sst_falsifier.runner import run_mode
        heartbeat.phase('framework_run',message='Framework preflight, backend probes and scientific run')
        exit_code=int(run_mode(ROOT,args.mode))
        raise SystemExit(exit_code)
    except SystemExit:
        raise
    except BaseException as exc:
        heartbeat.phase('exception',message=type(exc).__name__+': '+str(exc))
        raise
    finally:
        heartbeat.finish(exit_code)
