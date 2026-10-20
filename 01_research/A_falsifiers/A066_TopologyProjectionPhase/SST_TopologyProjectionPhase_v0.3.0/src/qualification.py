"""Numerical convergence summary (no scientific/fundamental SST certification)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def build(root=ROOT):
    out=root/'results/EULER_LONG'
    cases=['KP_3_1_N300','FS_knot_3_1','FS_knot_4_1','FS_knot_7_1','IL_L4a1']
    report={'normalization':'Periodic coordinate shortest displacement; same material labels and final time','status':'NUMERICAL_SCREEN_ONLY','cases':{},
    'numerical_gates':{'T_EQ_2p4':'PASS_IF_EQUAL','SIGMA_0p5':'PASS_IF_EQUAL',
      'RICHARDSON':'reported but not assumed to reach asymptotic regime','EULER_PHYSICAL':'UNRESOLVED'} }
    for name in cases:
        js={};ds={}
        for N,S in [(24,72),(32,96),(40,120)]:
            key=f'{name}_N{N}_S{S}_T2.4_SG0.5'
            x=json.loads((out/(key+'.json')).read_text());js[N]=x
            with np.load(out/(key+'.npz'),allow_pickle=False) as z:
                ds[N]={k:z[k] for k in z.files if k.endswith('_step_'+str(S))}
        marker_d=[]
        for na,nb in [(24,32),(32,40),(24,40)]:
            dif=[];total=0
            for i in range(len(js[na]['final_knot_dets'])):
                a=ds[na][f'component_{i}_step_{ {24:72,32:96,40:120}[na] }'];b=ds[nb][f'component_{i}_step_{ {24:72,32:96,40:120}[nb] }']
                d=(a-b+np.pi)%(2*np.pi)-np.pi
                dif.append(np.sum(d*d,axis=1));total+=len(a)
            rms=float(np.sqrt(np.sum(np.concatenate(dif))/total))
            marker_d.append({'grids':f'{na}-{nb}','rms_box_length':rms})
        ent={'grid_evolutions':[{k:v[k] for k in ('grid','steps','duration_model','sigma_model','sigma_over_dx','max_energy_relative_drift','max_helicity_relative_drift','max_kelvin_loop_relative_drift','initial_knot_dets','final_knot_dets','initial_linking','final_linking','topology_unchanged_screen','periodic_boundary_risk')} for v in js.values()],
         'same_time_marker_differences':marker_d,
         'spatial_marker_decrease_24_32_vs_32_40': bool(marker_d[1]['rms_box_length']<marker_d[0]['rms_box_length']),
         'topology_preserved_all_grids':all(x['topology_unchanged_screen'] for x in js.values()),
         'kelvin_error_decreasing_24_to_32_to_40':js[24]['max_kelvin_loop_relative_drift']>js[32]['max_kelvin_loop_relative_drift']>js[40]['max_kelvin_loop_relative_drift'],
         'scientific_qualification':'UNRESOLVED_FIXED_CORE_MODEL_AND_FULL_DYNAMIC_STABILITY'}
        report['cases'][name]=ent
    # Temporal comparison: same N, T, sigma and exact source geometry, dt halved.
    def load(name,N,S,sig):
        key=f'{name}_N{N}_S{S}_T2.4_SG{sig}'
        j=json.loads((out/(key+'.json')).read_text())
        with np.load(out/(key+'.npz'),allow_pickle=False) as z:x=z[f'component_0_step_{S}']
        return j,x
    ref=report['cases']['KP_3_1_N300']
    j1,x1=load('KP_3_1_N300',32,96,'0.5');j2,x2=load('KP_3_1_N300',32,192,'0.5')
    dt_res=float(np.sqrt(np.mean(np.sum(((x1-x2+np.pi)%(2*np.pi)-np.pi)**2,axis=-1))))
    ref['temporal_refinement_same_time_marker_rms']=dt_res
    ref['temporal_refinement_relative_to_spatial_32_40']=dt_res/max(ref['same_time_marker_differences'][1]['rms_box_length'],1e-30)
    core=[]
    for sig in ('0.4','0.6'):
        j,x=load('KP_3_1_N300',32,96,sig)
        rms=float(np.sqrt(np.mean(np.sum(((x1-x+np.pi)%(2*np.pi)-np.pi)**2,axis=-1))))
        core.append({'sigma':float(sig),'marker_rms_against_sigma0p5':rms,'kelvin_rel_drift':j['max_kelvin_loop_relative_drift']})
    ref['core_regularization_sensitivity']=core
    ref['core_qualification']='UNRESOLVED_ALTERNATIVE_CORE_WIDTH_IS_DIFFERENT_MODEL_NOT_NUMERIC_REFINEMENT'
    (root/'results/CONVERGENCE_ASSESSMENT.json').write_text(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    r=build()
    for key,item in r['cases'].items():print(key,item['topology_preserved_all_grids'],'marker',item['same_time_marker_differences'], 'kelvin_decr',item['kelvin_error_decreasing_24_to_32_to_40'])
    print('DT',r['cases']['KP_3_1_N300']['temporal_refinement_same_time_marker_rms'])
