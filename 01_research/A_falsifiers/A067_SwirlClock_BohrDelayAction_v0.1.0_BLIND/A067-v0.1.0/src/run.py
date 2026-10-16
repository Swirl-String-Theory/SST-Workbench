"""Independent baseline runner: test implementation gates; physical closure stays UNRESOLVED.
Usage: python src/run.py [--input other.npz] [--out PATH]
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
from core import find_branches,harmonic_action,rotor_action,euler_scaling_check,integrate_phase,sha256,dump,TAU
from inspect_pklsa import inspect

ROOT=Path(__file__).resolve().parents[1]

def run(input_dir:Path,output_dir:Path)->dict:
    output_dir.mkdir(parents=True,exist_ok=True)
    source_dir=ROOT/'inputs'
    cases=sorted(input_dir.glob('S*.npz'))
    if len(cases)!=3: raise RuntimeError('Expected exactly three pre-sealed control NPZ; found '+str(len(cases)))
    source_manifest=json.loads((input_dir/'SEALED_INPUT_MANIFEST.json').read_text(encoding='utf-8'))
    recorded={x['file']:x['sha256'] for x in source_manifest['files']}
    inputs_valid=all(sha256(p)==recorded.get(p.name) for p in cases)
    if not inputs_valid: raise RuntimeError('Source SHA256 tampering detected; fail closed')
    all_case=[]
    for p in cases:
        with np.load(p,allow_pickle=False) as z:
            theta0,beta,delay,inertia,mass=float(z['theta0']),float(z['beta']),float(z['delay_s']),float(z['inertia_kg_m2']),float(z['mode_mass_kg'])
            amp=z['amplitudes_m'].astype(float)
            roots=find_branches(theta0,beta)
            stable=[r for r in roots if r['stability']=='STABLE_SUFFICIENT' and r['theta']>0.01]
            chosen=stable[:len(amp)]
            if len(chosen)<len(amp):raise RuntimeError('not enough positive stable roots')
            actions=[];harmonic=[]
            for r,a in zip(chosen,amp):
                omega=r['theta']/delay
                actions.append(rotor_action(inertia,omega))
                harmonic.append(harmonic_action(mass,float(a),omega))
            dif=np.diff(actions)
            difharm=np.diff([x['J_num_Js'] for x in harmonic])
            omega=np.array([r['theta']/delay for r in chosen],dtype=float)
            normsp=float(np.std(dif)/np.mean(abs(dif))) if len(dif)>1 else float('nan')
            hnormsp=float(np.std(difharm)/np.mean(abs(difharm))) if len(difharm)>1 else float('nan')
            all_case.append({'case':p.stem,'source_sha256':sha256(p),'source_class':'synthetic_control',
                 'delay_s':delay,'beta':beta,'theta0':theta0,'stable_roots_total':len(stable),
                 'branch_theta':[r['theta'] for r in chosen],'branch_theta_residuals':[r['root_residual'] for r in chosen],
                 'A_tau':[r['A_tau'] for r in chosen], 'root_omega_rad_s':omega.tolist(),
                 'rotor_actions_Js':actions,'harmonic_actions_Js':[r['J_num_Js'] for r in harmonic],
                 'harmonic_integration_rel_error':[r['relative_error'] for r in harmonic],
                 'rotor_gap_cv':normsp,'harmonic_gap_cv':hnormsp,
                 'note':'Harmonic action and rotor action are different canonical model hypotheses; no h target is used'})
    # Exact closed-form and time-domain model qualification, not PKLSA dynamics
    center=TAU;beta=12.0
    numeric_1=integrate_phase(center,beta,center,step=0.005)
    numeric_2=integrate_phase(center,beta,center,step=0.0025)
    scale=euler_scaling_check(1.0,1.2,0.8,1.3)
    gaprat=[c['rotor_gap_cv'] for c in all_case]
    pklsa=inspect(input_dir/'PKLSA_STATIC_CANDIDATE_SURFACE.npz')
    if not pklsa['matches_pinned_static_pklsa']:
        raise RuntimeError('PKLSA static-source hash mismatch; fail closed')
    dump(output_dir/'PKLSA_EVIDENCE.json',pklsa)
    gates={
       'G0_SEALED_PROVENANCE':{'status':'PASS_CONTROL','metric':inputs_valid,'evidence_class':'synthetic_control'},
       'G1_ANALYTIC_FOURIER_ACTION':{'status':'PASS_CONTROL' if max(max(c['harmonic_integration_rel_error']) for c in all_case)<1e-10 else 'FAIL',
           'metric':max(max(c['harmonic_integration_rel_error']) for c in all_case),'threshold':1e-10},
       'G2_DELAY_ROOT_STABILITY':{'status':'PASS_CONTROL' if max(max(c['branch_theta_residuals']) for c in all_case)<1e-9 else 'FAIL',
           'metric':max(max(c['branch_theta_residuals']) for c in all_case),'threshold':1e-9},
       'G3_DELAY_TIME_DOMAIN':{'status':'PASS_CONTROL' if max(numeric_1['abs_error'],numeric_2['abs_error'])<0.015 else 'FAIL',
           'metric':{'coarse':numeric_1,'fine':numeric_2},'threshold_abs_theta':0.015},
       'G4_ACTION_FREQ_IDENT':{'status':'PASS_CONTROL' if all(c['rotor_gap_cv']<0.25 for c in all_case) else 'FAIL',
           'metric':gaprat,'note':'diagnostic only; finite K spacing is not exactly n*h'},
       'G5_AMPLITUDE_COUNTEREXAMPLE':{'status':'PASS_CONTROL' if any(c['harmonic_gap_cv']>c['rotor_gap_cv']*1.25 for c in all_case) else 'FAIL',
           'metric':[c['harmonic_gap_cv'] for c in all_case],
           'note':'checks that frequency discreteness cannot pass harmonic-action quantization'},
       'G6_EULER_SCALE_NULL':{'status':'PASS_CONTROL' if abs(scale['measured_ratio']-scale['predicted_ratio'])<1e-12 else 'FAIL',
           'metric':scale},
       'G7_REAL_3D_PHASE_DELAY':{'status':'UNRESOLVED','reason':'Actual PKLSA source is STATIC_GEOMETRY_ONLY; cannot reconstruct local phase or delay from vertices/triangles','upstream_source_check':pklsa['schema_kind']},
       'G8_CANONICAL_ACTION':{'status':'UNRESOLVED','reason':'No symplectic reduction / physical canonical momentum computed from 3D vortex field'},
       'G9_CLOCK_AND_H_CLOSURE':{'status':'UNRESOLVED','reason':'No observed d tau_clock/dT or target-blind independent action quantum'},
    }
    summary={'project':'SST_SwirlClock_BohrDelayAction','version':'v0.1.0','research_status':'UNRESOLVED_PHYSICAL',
          'framework_target':'SST Falsifier Framework v1.0.7 (not executed in isolated baseline)',
          'cases':all_case,'gates':gates,'publication_claim':'none; implementation controls only',
          'comparison_target_used_during_blind_fit':False}
    dump(output_dir/'GATE_RESULTS.json',summary)
    dump(output_dir/'GATE_LEDGER_STANDALONE.json',gates)
    dump(output_dir/'RUN_SUMMARY_STANDALONE.json',{'num_control_cases':len(cases),'num_pass_controls':sum(v['status']=='PASS_CONTROL' for v in gates.values()),
       'num_unresolved_physical':sum(v['status']=='UNRESOLVED' for v in gates.values()),'status':'UNRESOLVED_PHYSICAL'})
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'inputs');ap.add_argument('--out',type=Path,default=ROOT/'outputs');a=ap.parse_args()
    s=run(a.input,a.out)
    print(json.dumps({'status':s['research_status'],'gates':{k:v['status'] for k,v in s['gates'].items()}},indent=2))
    sys.exit(1 if any(v['status']=='FAIL' for v in s['gates'].values()) else 0)
