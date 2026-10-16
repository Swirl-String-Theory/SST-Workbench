"""A062-v0.3.0 native shared-framework science instance; no claim of a new GR derivation."""
from pathlib import Path
from microgravity.science_v030 import run

def run_scientific_pipeline(root:Path,cfg:dict,ledger,mode:str)->dict:
    ledger.record('G0','PASS',metrics={'framework':'1.0.8','release_status':'LOCAL_VALIDATED_CANDIDATE'},reason='Framework verified frozen protocol before entry')
    out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"
    result=run(out,mode)
    st={g['gate']:g for g in result['scientific_gates']}
    def add(gid,status,reason,metrics=None,authority='REFERENCE',backend='python-fp64'):
        if gid not in ledger.defs:return
        if not ledger.defs[gid].enabled:
            ledger.record(gid,'NOT_APPLICABLE',reason='Disabled by framework profile');return
        ledger.record(gid,status,reason=reason,metrics=metrics or {},authority=authority,actual_backend=backend)
    add('G1',st['M0']['status'],'Two E011 source-original hashes match registered carriers',{'source_anchors':2,'STATIC_READY_not_DYNAMICS_READY':True})
    add('G2','PASS' if all(st[k]['status']=='PASS' for k in ['M1','M2','M3','M4','M6']) else 'FAIL','Euler zero monopole theorem, normalized scalar EFT solution, force and cross-stress numerical controls',{'M1':st['M1']['metric'],'M2':st['M2']['metric'],'M4':st['M4']['metric']})
    add('G3',st['M7']['status'],'Direct Euler pressure-source-to-clock-charge identification cannot yield nonzero monopole; do not generalize to all SST clock theories',{'Q_pressure':0,'H1_conditional_slope':st['M2']['metric']})
    add('G4','UNRESOLVED','Public paper benchmark exists, no heldout raw force distance measurements')
    q=result['native_cpp_fp64'];add('G5',q['status'],'Actual independent compiled C++17 FP64 normalized EFT pair kernel',q,authority='CERTIFICATION' if q['status']=='PASS' else 'NONE',backend='cpp-fp64' if q.get('executed') else 'unavailable')
    add('G6','UNRESOLVED','No GPU screening requested',authority='NONE',backend='not_requested')
    add('G7','PASS' if st['M5']['status']=='PASS' and st['M2']['status']=='PASS' else 'FAIL','Two independent static geometry providers agree for conditional postulated scalar EFT',{'provider_amplitude_relative_diff':result['provider_amplitude_difference_R5']})
    add('G8','UNRESOLVED','No derived charge, scalar mode, dimensional normalization, macroscopic mass model or full Euler resolved stress closure',{'clock_charge_derived':False,'G_derived':False})
    return {'schema':'SST-BACKEND-MANIFEST-2','python_reference':{'actual_backend':'python-numpy-fp64','precision':'float64','authority':'REFERENCE'},'cpp_fp64':q,'sycl_gpu':{'requested':False,'authority':'SCREENING_ONLY'},'scientific_boundary':'H1 inverse-square is a conditional result with explicitly postulated scalar charge and coupling; H2 bridge not proven'}
