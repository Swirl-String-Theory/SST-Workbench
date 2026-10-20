"""Optional E010 v0.3.2 -> framework v1.0.10 REAL GateLedger bridge.

Not a frozen framework instance: it only emits an independent diagnostic ledger.
Requires the exact framework installation, never silently uses another copy.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

def emit(report, framework_root, output):
    root=Path(framework_root).resolve()
    meta=root/'RELEASE_INFO.json'
    if not meta.is_file() or not (root/'sst_falsifier'/'gates.py').is_file():
        raise RuntimeError('No complete framework release at specified root')
    rel=json.loads(meta.read_text(encoding='utf-8'))
    if rel.get('version')!='1.0.10':
        raise RuntimeError('Wrong framework version, expected 1.0.10')
    sys.path.insert(0,str(root))
    import sst_falsifier.gates as gates
    if not Path(gates.__file__).resolve().is_relative_to(root):
        raise RuntimeError('Framework loaded from non-pinned path; fail closed')
    definitions=[
        gates.GateDefinition('DYN0','Verified upstream E011 primary original source SHA?'),
        gates.GateDefinition('DYN1','Finite-core spatial resolution qualified?',('DYN0',)),
        gates.GateDefinition('DYN2','Biot-Savart velocity spatial convergence?',('DYN0',)),
        gates.GateDefinition('DYN3','RK4 time-step convergence and order?',('DYN0',)),
        gates.GateDefinition('DYN4','Energy, filament length, nonlocal gap screening?',('DYN0',)),
        gates.GateDefinition('DYN5','Numerical filament model dynamics-ready?',('DYN1','DYN2','DYN3','DYN4')),
        gates.GateDefinition('DYN6','Full incompressible 3D Euler dynamics validated?',('DYN5',)),
        gates.GateDefinition('DYN7','Independently computed intrinsic Swirl Clock?',('DYN6',))]
    ledger=gates.GateLedger(definitions)
    for full_gate_name,r in report['dynamic_gate_ledger'].items():
        gid=full_gate_name.split('_',1)[0]
        ledger.record(gid,r['status'],reason=r.get('reason',''),
                      execution_status=r.get('execution_status','EXECUTED'),
                      metrics=report['metrics'] if gid=='DYN5' else {},
                      requested_backend='NumPy-FP64 filament Biot-Savart' if gid in ('DYN1','DYN2','DYN3','DYN4','DYN5') else None,
                      actual_backend='NumPy-FP64 filament Biot-Savart' if gid in ('DYN1','DYN2','DYN3','DYN4','DYN5') else None,
                      authority='NUMERICAL_FILAMENT_ONLY' if gid=='DYN5' else None)
    output=Path(output)
    if output.exists():raise RuntimeError('Ledger destination exists: no overwrite')
    ledger.write(output)
    return ledger.to_dict()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--framework-root',required=True)
    ap.add_argument('--run-result',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args()
    obj=json.loads(Path(args.run_result).read_text())
    v=emit(obj,args.framework_root,args.out)
    print('v1.0.10 GateLedger SHA256:',v['ledger_sha256'])
    print('DYN5:',next(r for r in v['records'] if r['gate_id']=='DYN5')['qualification'])
    print('DYN6:',next(r for r in v['records'] if r['gate_id']=='DYN6')['status'])
if __name__=='__main__':main()
