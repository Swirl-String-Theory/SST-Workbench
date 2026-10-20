#!/usr/bin/env python3
"""Call ACTUAL external framework v1.0.10 GateLedger, preserving full diagnostic semantics.

This is an adapter ONLY, not an official framework instance, blind run or signed reveal.
Never import or silently substitute v1.0.9. Requires explicit --framework-root.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from gp_full_xpu import json_exclusive,sha256

def run(result_json,root):
    root=Path(root).resolve()
    release=root/'RELEASE_INFO.json'
    if not release.is_file():raise FileNotFoundError('framework v1.0.10 RELEASE_INFO.json not found')
    info=json.loads(release.read_text(encoding='utf8'))
    if str(info.get('version'))!='1.0.10':
        raise ValueError('FAIL_CLOSED: expected EXACT framework v1.0.10; got '+repr(info.get('version')))
    sys.path.insert(0,str(root))
    # Import here, never allow accidental framework fallback via ambient PYTHONPATH.
    import sst_falsifier.gates as gates
    origin=Path(gates.__file__).resolve()
    if root not in origin.parents:raise RuntimeError('framework import escaped explicit v1.0.10 root')
    result=json.loads(Path(result_json).read_text(encoding='utf8'))
    if result.get('schema')!='A069-V063-FULL-GPU-DEVELOPMENT-1':raise ValueError('not an A069 v0.6.3 FULL result')
    pre=result['g32_screen']['all_preconditions_met']
    parity=result['cpu_fp64_parity']
    defs=[
       gates.GateDefinition('G31','Independent dynamics source capable of physical PKLSA clock certification?'),
       gates.GateDefinition('G32','Source-native finite core geometry+grid screening?',requires=('G31',)),
       gates.GateDefinition('G33','Time-resolved, unambiguous subgrid filament reconstruction?',requires=('G32',)),
       gates.GateDefinition('G34','Continuous knot-topology and convergence certificate?',requires=('G33',)),
       gates.GateDefinition('G35','Independent stable reduced Floquet mode and clock holdout?',requires=('G34',)),
       gates.GateDefinition('G36','XPU versus CPU FP64 short numerical parity screening?'),
    ]
    ledger=gates.GateLedger(defs,strict_dependencies=False)
    def output():
        if parity['status']=='PASS_NUMERICAL_SCREENING' and result['xpu_used']:
            return {'status':'PASS','metrics':{'relative_l2':parity.get('relative_l2'),'steps':parity.get('steps')},
                    'reason':'SHORT numeric parity only; no knot topology/physics','actual_backend':'torch-xpu-fp32',
                    'requested_backend':'torch-xpu-fp32','authority':'SCREENING_ONLY_CPU_FP64_REFERENCE'}
        return {'status':'UNRESOLVED','reason':'GPU parity unavailable, unqualified, or CPU-only smoke'}
    ledger.run_evaluators({
      'G31':lambda:{'status':'UNRESOLVED','reason':'Independent physical PKLSA/clock source not supplied'},
      'G32':lambda:{'status':'PASS' if pre else 'FAIL','metrics':result['g32_screen'],
                    'reason':'This is a geometric source screen, not dynamics'},
      'G33':lambda:{'status':'UNRESOLVED','reason':'offline topological snapshot diagnostic not included here'},
      'G34':lambda:{'status':'UNRESOLVED','reason':'continuous isotopy/convergence not certified'},
      'G35':lambda:{'status':'UNRESOLVED','reason':'reduced knot mode and physical clock remain unresolved'},
      'G36':output,
    })
    return {'schema':'A069-V063-FRAMEWORK-1.0.10-REAL-LEDGER-ADAPTER-1',
      'framework_source_root':str(root),'framework_version':info['version'],
      'framework_release_status':info.get('status'),'gate_code_sha256':sha256(origin),
      'framework_ledger_called':True,'framework_official_instance_executed':False,
      'blind_reveal_permitted':False,
      'source_result_sha256':sha256(Path(result_json)),
      'gates':{d.gate_id:{'status':ledger.status(d.gate_id),**ledger.qualification(d.gate_id)} for d in defs},
      'warning':'GateLedger use does not constitute source freeze, signed protocol, hardware selftest or official BLIND instance.'}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--framework-root',type=Path,required=True)
    a.add_argument('--result',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    x=a.parse_args();out=run(x.result,x.framework_root);json_exclusive(x.out,out)
    print(json.dumps({'output':str(x.out),'G32':out['gates']['G32'],'G35':out['gates']['G35'],
       'official_instance':False},indent=2))
if __name__=='__main__':main()
