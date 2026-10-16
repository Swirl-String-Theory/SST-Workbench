from __future__ import annotations
import argparse,json,sys,tempfile
from pathlib import Path
from common import digest,dump,read,unique,guard,sha_record

BASE=Path(__file__).resolve().parent
REGISTRY=BASE/'identity_registry.json'
INPUTS=BASE/'inputs.json'
FREEZE=BASE/'frozen_contract.json'

def preflight():
    r=read(REGISTRY)
    guard(r['A045']['scientific_name']=='Two_Harmonic_Phase_Chirality_Floquet','A045 name conflict: STOP')
    guard(r['A046']['scientific_name']=='Relative_Vorticity_Triadic_Geometry','A046 name conflict: STOP')
    guard(r['A058']['scientific_name']=='KnotPlot_Parameter_Sensitivity_Relaxation_Robustness', 'A058 name conflict: STOP')
    guard(r['A060']['scientific_name']=='Dynamical_Topology_Coherence','A060 family name conflict: STOP')
    cfg=read(INPUTS)
    guard(sorted(cfg['sources'])==sorted(['A045','A046','A058','A054']), 'Missing required input keys')
    return cfg

def source_bindings():
    cfg=preflight(); files={}
    for k,fn in cfg['sources'].items():
        if not fn:continue
        p=Path(fn)
        if not p.is_absolute():p=(BASE/p).resolve()
        guard(p.is_file(),f'{k} source missing: {p}')
        files[k]={'path':str(p),'sha256':digest(p),'size_bytes':p.stat().st_size}
    return files

def freeze():
    guard(not FREEZE.exists(),'Frozen contract exists; new version required for any changes')
    cfg=preflight()
    sha={'identity_registry':digest(REGISTRY),'inputs':digest(INPUTS)}
    frozen=source_bindings()
    dump(FREEZE,{'schema':'SST-A060v030-POSTRUN-RECONCILIATION-FREEZE','protocol_shas':sha,
        'sources':frozen,'scope':'POSTRUN_AUDIT_NOT_NEW_BLIND_EXPERIMENT',
        'original_falsifier_source_mutated':False})
    print('A060 postrun audit inputs frozen (no physics campaign run).',FREEZE)

def extract(file):
    try:return read(file)
    except (ValueError,UnicodeDecodeError):raise ValueError(f'Expected machine-readable JSON, not PDF/ZIP: {file}')

def analyze_one(k,v):
    if k=='A045':
        gates=v.get('gates',{})
        return {'item':'A045_RPO_FLOQUET', 'status':'QUALIFIED_LINEAR_ONLY' if gates.get('G5_TRANSVERSE_FLOQUET')=='PASS_LINEAR_MODEL' else 'UNRESOLVED',
                'evidence':gates.get('G5_TRANSVERSE_FLOQUET','MISSING'),
                'restriction':'A045 v0.2.2 has physics UNTESTED; full Euler/held-out source separately required'}
    if k=='A046':
        gates=v.get('gates',{})
        return {'item':'A046_PKLSA_FIELD','status':'UNRESOLVED',
                'evidence':{'boundary':gates.get('G5_BOUNDARY_PHYSICAL_CLOSURE','MISSING'),
                            'euler':gates.get('G6_EULER_TIME_EVOLUTION','MISSING'),
                            'independent_provider':gates.get('G7_INDEPENDENT_PROVIDER_REPLICATION','MISSING')},
                'restriction':'G0-G4 numerical diagnostics are not physical gravity closure'}
    if k=='A058':
        return {'item':'A058_REAL_KNOTPLOT','status':'UNRESOLVED',
                'evidence':{'source_mode':v.get('requested_mode',v.get('mode','UNKNOWN')),
                            'process_exit_code':v.get('exit_code','UNKNOWN')},
                'restriction':'A successful process exit does not establish 271 eligible hardware cases, convergence, or physical stability'}
    if k=='A054':
        return {'item':'A054_PROVIDER_STATE_SELECTION','status':'UNRESOLVED',
                'evidence':v.get('scientific_verdict',v.get('physics_verdict',v.get('status','UNRESOLVED'))),
                'restriction':'Latest v0.5.1 result is unresolved; independent provider/state endpoints needed'}
    raise AssertionError(k)

def aggregate():
    guard(FREEZE.exists(),'Must FREEZE identity and evidence inputs first')
    fr=read(FREEZE)
    guard(fr['protocol_shas']=={'identity_registry':digest(REGISTRY),'inputs':digest(INPUTS)},
         'Frozen protocol hash mismatch: new A060 version required')
    guard(fr['sources']==source_bindings(),'Frozen input content changed: cannot aggregate')
    rows=[]
    for k in ('A045','A046','A058','A054'):
        obj=fr['sources'].get(k)
        rows.append(analyze_one(k,extract(obj['path'])) if obj else {'item':k,'status':'NOT_RUN','reason':'No frozen machine-readable evidence supplied'})
    rows.append({'item':'A060_M05_M08_PHYSICAL_INTEGRATION',
                 'status':'UNRESOLVED','reason':'No promoted 3D Euler, independent RPO, or target-free gravity coupling via this postrun audit'})
    rows.append({'item':'A045_IDENTITY_RECONCILIATION',
                 'status':'PASS_REGISTRY_MAPPING_ONLY','reason':'A045 is Two-Harmonic Floquet; relative vorticity is A046'})
    out=unique(BASE/'outputs','A060v030')
    dump(out/'GATE_LEDGER.json',{'schema':'SST-A060v030-POSTRUN-RECONCILIATION',
          'gates':rows,'overall':'UNRESOLVED_PHYSICAL_CLOSURE','physics_claim':'NONE',
          'source_fingerprints':fr['sources'],'blind_prospective':False})
    dump(out/'RUN_SUMMARY.json',{'mode':'POSTRUN_AUDIT','source_frozen':True,
         'identity_conflict':'RESOLVED_IN_BRIDGE_ONLY_NOT_IN_LEGACY_REGISTRY',
         'physical_simulation_ran':False,'physical_verdict':'UNRESOLVED'})
    print(out,'\n'+json.dumps(rows,indent=2))

def selftest():
    preflight()
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'input.json';p.write_text(json.dumps({'gates':{'G5_TRANSVERSE_FLOQUET':'NOT_RUN'}}))
        assert analyze_one('A045',read(p))['status']=='UNRESOLVED'
        assert analyze_one('A058',{'exit_code':0})['status']=='UNRESOLVED'
    print('A060 SELFTEST PASS (mock gate parsers; cross-source physical evidence NOT_RUN)')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['SELFTEST','FREEZE','RUN'])
    a=p.parse_args()
    {'SELFTEST':selftest,'FREEZE':freeze,'RUN':aggregate}[a.mode]()
if __name__=='__main__':
    try:main()
    except Exception as e:print('FAIL-CLOSED:',e,file=sys.stderr);sys.exit(2)
