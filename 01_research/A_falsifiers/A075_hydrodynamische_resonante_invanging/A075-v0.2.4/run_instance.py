from __future__ import annotations
from pathlib import Path
import json,os,sys
from runtime_options import parse
ROOT=Path(__file__).resolve().parent

if __name__=='__main__':
    args,overrides,plan=parse(sys.argv[1:])
    if args.plan:
        from experiment.science import probe_backend
        probe={x:probe_backend(x,ROOT) for x in overrides.get('backends',[])}
        print(json.dumps({'mode':args.mode,'plan':plan,'backend_preflight':probe,
                          'status':'PLAN_ONLY_NOT_EXECUTED'},indent=2))
        raise SystemExit(0)
    if args.mode=='GPU_PROBE':
        from framework_bootstrap import load_framework
        framework=load_framework()
        from sst_falsifier.sycl_worker import probe_worker
        from tools.gpu_probe import stage_template_worker
        from experiment.science import save
        stage=stage_template_worker(framework,ROOT)
        probe=probe_worker(ROOT) if stage.get('success') else {'available':False,'error':stage.get('reason')}
        from experiment.science import probe_backend
        xpu=probe_backend('gpu',ROOT)
        evidence={'schema':'A075-MULTI-GPU-DEVICE-PROBE-2','framework_version':'1.0.10',
            'template_source_staging':stage,'probe':probe,'pytorch_xpu_euler_probe':xpu,'gpu_euler_backend_certified':False,
            'qualification':'DEVICE_DIAGNOSTIC_ONLY','sycl_worker_is_gpu':bool(probe.get('is_gpu',False)),
            'reason':'Framework SYCL worker computes Biot-Savart, not the A075 FFT/Leray/RK4 Euler solver'}
        save(ROOT/'diagnostics'/'arc_device_probe.json',evidence)
        print(json.dumps(evidence,indent=2))
        raise SystemExit(0 if xpu.get('available') and probe.get('available') and probe.get('is_gpu') else 2)
    if args.mode=='PREVIEW':
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
        raise SystemExit(0)
    # Bound OpenMP to the same explicitly requested CPU worker count.
    os.environ['OMP_NUM_THREADS']=str(args.threads)
    os.environ['OMP_DYNAMIC']='FALSE'
    # This environment is transmitted only to the Framework's actual science adapter.
    # All scientific choices are written in A075_GATES.json and BACKEND_MANIFEST.json.
    os.environ['A075_RUNTIME_OPTIONS_JSON']=json.dumps(overrides,sort_keys=True)
    from framework_bootstrap import load_framework
    load_framework()
    from sst_falsifier.runner import run_mode
    raise SystemExit(run_mode(ROOT,args.mode))
