"""Bounded, checkpointed numerical Euler validation campaign at fixed T=0.10 s.

This is an explicitly reduced exploratory campaign, not the preregistered full
T=0.4s run, nor a runtime framework FREEZE/FULL certification.
"""
from __future__ import annotations
import json,hashlib
from pathlib import Path
import numpy as np
from .euler3d import Euler3D
from .model import sample_seed,load_seed,relative_equilibrium_residual,min_nonlocal_distance
from .run_euler import run_sim,independent_perturbation,sha

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Trefoil_Max_Transfer_Force_v0.2.0-outputs'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    seed=load_seed(ROOT/'seeds/trefoil_ideal_3_1_1.json')
    x=sample_seed(seed,128)
    # Keep the 9-case candidate fixed based on previous target-free discovery:
    core=.28; x=x.copy();x[:,2]*=1.15
    T=.10; dt=.0125; steps=8
    report={'schema':'SST-3D-EULER-PILOT-V020','status':'PILOT_NOT_CERTIFIED',
            'framework_version_pin':'1.0.10','framework_run_performed':False,
            'source_id':seed['id'],'source_hash':seed['source_sha256'],
            'fixed_final_time_s':T,'dt_s':dt,'steps':steps,
            'core_width_m':core,'density_kg_m3':1.,'circulation_m2_s':1.,
            'box_side_m':6.,'core_evolution':'3D_EULER_DISTRIBUTED_VORTICITY',
            'force_coupling':'BOX_WIDE_DIVERGENCE_FREE_SHEAR_NOT_PHYSICAL_CLAMPS',
            'initial_selection':'fixed prior to pilot: a=0.28, zscale=1.15, nine-case Euler residual scan',
            'scenarios':[],'perturbations':[], 'time_refinement':None,
            'failure_limits':'UNRESOLVED: finite-time shear response is not ultimate transferable force'}
    def checkpoint():
        (OUT/'PILOT_EULER_REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    for n in [32,48,64]:
        m=Euler3D(n,6,1)
        base=m.omega_initial(x,core,1)
        fit=relative_equilibrium_residual(x,m.sample(m.ifft(base),x))
        err=np.linalg.norm(m.rhs(base)-m.rhs(base,form='convective'))/np.linalg.norm(m.rhs(base))
        for force in [0.,.1,1.6]:
            uh,material,d=run_sim(m,base,x,force,steps,T,core)
            report['scenarios'].append({'n':n,'core_cells':core/m.dx,'forcing_m_s2':force,
                           'initial_relative_equilibrium_error':fit['normal_residual'],
                           'rotational_vs_convective_rhs_relative':float(err),**d})
            checkpoint()
            print(f"n={n} force={force}: energy drift={d['energy_drift_relative']:.3g}, gap/core={d['gap_over_2_core']:.3g}",flush=True)
        if n in [48,64]:
            for mode in (['z2','x3'] if n==48 else ['z2']):
                datum=independent_perturbation(m,x,core,.1,steps,T,.01,mode)
                report['perturbations'].append({'n':n,**datum})
                checkpoint()
                print(f"n={n} perturb={mode}: growth={datum['max_growth']:.5g}",flush=True)
        if n==48:
            _,_,fine=run_sim(m,base,x,0.,2*steps,T,core)
            base_stat=next(x for x in report['scenarios'] if x['n']==48 and x['forcing_m_s2']==0)
            report['time_refinement']={
                'n':48,'fixed_final_time_s':T,'dt_coarse_s':dt,'dt_fine_s':dt/2,
                'relative_energy_difference':abs(fine['energy_J']-base_stat['energy_J'])/abs(fine['energy_J']),
                'relative_material_length_difference':abs(fine['material_marker_length_m']-base_stat['material_marker_length_m'])/fine['material_marker_length_m']}
            checkpoint()
    baseline=[z for z in report['scenarios'] if z['forcing_m_s2']==0.]
    lengths=[z['material_marker_length_m'] for z in baseline]
    report['spatial_energy_disagreement_48_64']=abs(baseline[2]['energy_J']-baseline[1]['energy_J'])/max(abs(baseline[2]['energy_J']),1e-30)
    report['spatial_length_disagreement_48_64']=abs(lengths[2]-lengths[1])/max(abs(lengths[2]),1e-30)
    report['gates']={
        'P0_source':'PASS_GILBERT_SINGLE_SOURCE',
        'P1_divergence_poisson':'PASS' if all(z['divergence_relative_residual']<1e-10 and z['poisson_relative_residual']<1e-10 for z in report['scenarios']) else 'FAIL',
        'P2_short_energy_conservation':'PASS' if all(abs(z['energy_drift_relative'])<.01 for z in baseline) else 'FAIL',
        'P3_relative_equilibrium':'FAIL' if min(z['initial_relative_equilibrium_error'] for z in baseline)>.05 else 'CANDIDATE_ONLY',
        'P4_independent_perturbations':'DIAGNOSTIC_ONLY',
        'P5_transferred_force':'UNRESOLVED_NOT_MEASURED',
        'P6_nonlinear_stability':'UNRESOLVED_NO_EQUILIBRIUM',
        'P7_long_time_convergence':'NOT_RUN_PREREQUISITE'
    }
    checkpoint()
    manifest={p.name:sha(p) for p in sorted(OUT.glob('*.json')) if p.name!='OUTPUT_MANIFEST_SHA256.json'}
    (OUT/'OUTPUT_MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('DONE',json.dumps({'gates':report['gates'],'spatial_disagreements': [report['spatial_energy_disagreement_48_64'],report['spatial_length_disagreement_48_64']],'perturbations':report['perturbations']},indent=2),flush=True)
    return report

if __name__=='__main__':main()
