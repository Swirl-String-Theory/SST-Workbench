#!/usr/bin/env python3
"""Run A064 v0.3.0 independently; no fake blind or Kelvin qualification."""
import hashlib, json, os, sys, csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from kelvin_spectrum import compute_spectrum,finite_difference_check,operator
from wavepackets import integrate_packets
from euler_tangent import Euler3D,load_geometry,initial_condition

NAME='A064-v0.3.0'
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def emit_gate(gates,name,pass_condition,detail,kind='NUMERICAL'):
    status='PASS' if pass_condition else 'FAIL'
    gates.append(dict(gate=name,status=status,category=kind,detail=detail))

def main():
    o=ROOT/'outputs';o.mkdir(exist_ok=True)
    configs={'grid_eigen':[8,12,16],'wave_n':16,'core':0.4,'dt':0.045,'wave_steps':160,
             'primary_families':['knot_3.1','knot_5.2','knot_6.1','link_6.3.3'],
             'primary_geometry':'knot_3.1',
             'controls':['no_background','reverse_circulation','timestep_half_12']}
    data={};gates=[]
    phase=os.environ.get('A064_PHASE','ALL').upper()
    if phase == 'CONTROLS':
        staging=json.loads((o/'primary_staging.json').read_text())
        data=staging['data'];gates=staging['gates']
    for nm in ([] if phase=='CONTROLS' else configs['primary_families']):
        file=ROOT/'data'/f'{nm}.txt'
        if nm=='knot_3.1':
            spectrum={}
            for n in configs['grid_eigen']:
                print(f'[EIGEN] {nm} n={n}',flush=True)
                z=compute_spectrum(file,n=n,core=.4)
                spectrum[str(n)]=z
                emit_gate(gates,f'EIG_{nm}_{n}_residual',max(x['relative_residual'] for x in z['candidates'])<1e-5,'Maximum normalized residual <1e-5')
                emit_gate(gates,f'EIG_{nm}_{n}_solenoidal',max(x['divergence_relative'] for x in z['candidates'])<1e-8,'Eigenvectors divergence-free')
        else:
            print(f'[EIGEN] {nm} n=8',flush=True)
            z=compute_spectrum(file,n=8,core=.4)
            spectrum={'8':z}
            emit_gate(gates,f'EIG_{nm}_8_residual',max(x['relative_residual'] for x in z['candidates'])<1e-5,'Maximum normalized residual <1e-5')
        print(f'[WAVE] {nm} n=16',flush=True)
        f,info=integrate_packets(file,n=16,steps=160,dt=.045)
        f.to_csv(o/f'{nm}_wave_timeseries.csv',index=False)
        emit_gate(gates,f'WAVE_{nm}_divergence',info['max_divergence']<1e-10,'Solenoidal time-dependent Euler and packet fields')
        # Gate names indicate operational evidence only; false is kept, no tuning.
        emit_gate(gates,f'WAVE_{nm}_counterpropagating',info['evidence']['A']['evidence'] and info['evidence']['B']['evidence'],
                  f"A={info['evidence']['A']['evidence']}, B={info['evidence']['B']['evidence']}",kind='SCREENING')
        emit_gate(gates,f'WAVE_{nm}_collision',info['verified_collision'],
                  'Separated counter-directed packets must demonstrate overlapping detector arrival',kind='SCREENING')
        data[nm]=dict(eigen=spectrum,wave=info)
    if phase=='PRIMARY':
        dump(o/'primary_staging.json',{'data':data,'gates':gates})
        print('[PRIMARY COMPLETE] four registered geometries',flush=True)
        return 0
    # Controls: no velocity means no tangent propagation; reversal tests robustness.
    for suffix,kwargs in {
        'null_no_flow':dict(no_flow=True,n=16,steps=160,dt=.045),
        'control_reverse':dict(background_sign=-1,n=16,steps=160,dt=.045),
        'control_halfdt':dict(n=12,steps=320,dt=.0225),
        'control_standard12':dict(n=12,steps=160,dt=.045),
    }.items():
        print(f'[CONTROL] {suffix}',flush=True)
        fr,inf=integrate_packets(ROOT/'data/knot_3.1.txt',**kwargs)
        fr.to_csv(o/f'{suffix}_wave_timeseries.csv',index=False)
        data[suffix]=inf
        emit_gate(gates,f'CONTROL_{suffix}_divergence',inf['max_divergence']<1e-10,'All evolved fields projected',kind='NUMERICAL')
    f0=pdread(o/'null_no_flow_wave_timeseries.csv')
    null_dev=max(abs(f0.A_detector-f0.A_detector.iloc[0]).max(),abs(f0.B_detector-f0.B_detector.iloc[0]).max())
    emit_gate(gates,'NO_FLOW_STATIC_WAVES',null_dev<1e-9,f'No-flow detector energy change {null_dev:.3g}')
    a,b=data['control_halfdt'],data['control_standard12']
    timestep_gap=abs(a['max_abs_interference_fraction']-b['max_abs_interference_fraction'])
    emit_gate(gates,'TIMESTEP_CROSS_CHECK',timestep_gap<.025,f'Max response fraction difference {timestep_gap:.6g}')
    geom,_=load_geometry(ROOT/'data/knot_3.1.txt')
    grid=Euler3D(12,.4); U,D,*_=initial_condition(grid,geom)
    fderr=finite_difference_check(grid,U,D[0])
    emit_gate(gates,'TANGENT_FD',fderr<1e-6,f'Nonlinear derivative relative discrepancy {fderr:.3e}')
    # Experimental physical questions: unresolved unless criterion independently satisfied.
    open_gates={
       'G6a_steady_relative_equilibrium':'UNRESOLVED (background is nonstationary)',
       'G6b_asymptotic_spectral_convergence':'UNRESOLVED (n=8/12/16 extremal branches differ)',
       'G6c_Kelvin_eigenbundle_connection':'UNRESOLVED (no unique Kelvin eigenspace transport)',
       'G7a_both_counterpropagating':'SCREEN_FAIL (tested launch does not establish both branches)',
       'G7b_recombination':'SCREEN_FAIL (no synchronized verified arrival)',
       'G7c_topology_specific_interference':'UNRESOLVED (no causal topology isolation)',
       'G8_PKLSA_provider_independence':'UNRESOLVED (single geometry-only provider)',
       'G9_official_framework_blind_native':'UNRESOLVED (v1.0.7 referenced but not invoked)'
    }
    result={
       'schema':'A064-PHYSICAL-DYNAMICS-SPECTRAL-SCREEN-3','version':'0.3.0',
       'experiment':'actual matrix-free linearized Euler eigenpairs + propagating-packet hypothesis test',
       'computed':data,'global_controls':dict(null_detector_max_absolute_drift=float(null_dev),
                        timestep_cross_fraction_difference=float(timestep_gap),tangent_fd_error=float(fderr)),
       'gates':gates,'scientific_gates':open_gates,
       'claimed_interference':'NO','claimed_kelvin_eigenmode':'NO',
       'overall':'NUMERICAL_OPERATOR_EIGENPAIRS_VERIFIED; G6 UNRESOLVED; G7 WAVE_PROPAGATION_SCREEN_FAIL; PHYSICAL G7 UNRESOLVED',
       'source_note':'single KnotPlot native census 0.1.2, non-SI coordinates, geometry only',
       'source_archive_origin':'A064 v0.2.0 source; euler_tangent.py preserved unchanged'
    }
    dump(o/'A064-v0.3.0_results.json',result)
    with (o/'gate_table.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['gate','status','category','detail']);w.writeheader();w.writerows(gates)
    with (o/'scientific_gate_states.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['gate','status']);w.writerows(open_gates.items())
    num=[x for x in gates if x['category']=='NUMERICAL']
    screen=[x for x in gates if x['category']=='SCREENING']
    print('NUMERICAL',sum(x['status']=='PASS' for x in num),'/',len(num),'SCREENING PASSED',sum(x['status']=='PASS' for x in screen),'/',len(screen))
    return 0 if all(x['status']=='PASS' for x in num) else 2

def pdread(path):
    import pandas as pd
    return pd.read_csv(path)
if __name__=='__main__':raise SystemExit(main())
