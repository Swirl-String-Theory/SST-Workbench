#!/usr/bin/env python3
"""F005 v0.5.0 E0 diagnostic: source claims, TRAIN-only relative polarity and start state.

No configuration changes; no TEST/OOD responses accessed; no promotion of certification.
Dependencies: numpy; Python >=3.10. Does not read DATASET.zip (49.9 GB).
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

EXPECTED_SPLIT_SHA256 = 'd60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2'
EXPECTED_INPUT_SHA256 = '5d51b77ecf20cc4327c11a416e5e70c42a63c8499b8f9ba7c0af1fdc35af3aed'
GEOMETRY = {'tank_length_internal_m': 0.080, 'tank_width_internal_m':0.031, 'fill_depth_m':0.043,
            'sensor_x_from_center_m':0.040,'liquid_density_kg_m3':998.0,
            'surface_tension_N_m':0.0,'gravity_m_s2':9.81,'n_modes':4}


def hash_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for buf in iter(lambda:f.read(1<<20),b''):
            h.update(buf)
    return h.hexdigest()


def load_locked_train_split(p):
    if hash_file(p)!=EXPECTED_SPLIT_SHA256:
        raise ValueError('LOCKED_V043_SPLIT_SHA256_MISMATCH')
    with open(p,newline='',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=4250: raise ValueError('SPLIT_ROW_COUNT_CHANGED')
    allids=[int(r['row_id_zero_based']) for r in rows]
    if len(set(allids))!=4250 or not all(0<=i<5000 for i in allids):
        raise ValueError('INVALID_OR_PROTECTED_ROW_IN_DEVELOPMENT_SPLIT')
    train=[int(r['row_id_zero_based']) for r in rows if r['partition']=='DEV_TRAIN']
    valid=[int(r['row_id_zero_based']) for r in rows if r['partition']=='DEV_VALIDATION']
    if len(train)!=3400 or len(valid)!=850:
        raise ValueError('LOCKED_DEVELOPMENT_SPLIT_COUNT_CHANGED')
    groups={}
    for r in rows: groups.setdefault(r['proxy_component_id'],set()).add(r['partition'])
    if any(len(q)>1 for q in groups.values()):
        raise ValueError('PROXY_FAMILY_CROSS_SPLIT')
    return sorted(train)


def geometry_documentation_check(cfg):
    comp={}
    for key,value in GEOMETRY.items():
        obs=cfg.get(key)
        comp[key]={'expected':value,'configured':obs,'match':obs is not None and
                   (abs(float(obs)-float(value)) < 1e-9)}
    missing=[k for k in ('acceleration_axis_sign','measurement_height_sign') if cfg.get(k) not in (-1,1)]
    open_flags={k: cfg.get(k) is not True for k in ('provenance_confirmed','initial_equilibrium_confirmed')}
    return comp,missing,open_flags


def model_from_rest(a,dt=0.004,n_modes=4):
    """Thesis geometry, sigma=0, two signed relative-polarity hypotheses.
    The output uses x=L/2, with +a and +right-wall sign in positive branch.
    TEST/OOD or validation arrays must never be passed into this audit.
    """
    a=np.asarray(a, dtype=float)
    L,h,x,rho,sig,g=(GEOMETRY[k] for k in ('tank_length_internal_m','fill_depth_m',
            'sensor_x_from_center_m','liquid_density_kg_m3','surface_tension_N_m','gravity_m_s2'))
    n=np.arange(n_modes)
    k=(2*n+1)*np.pi/L
    omega=np.sqrt((g*k+sig/rho*k**3)*np.tanh(k*h))
    coef=-k*np.tanh(k*h)*(4*(-1.)**n/(L*k*k))
    shape=np.sin(k*x)
    q=np.zeros((a.shape[0],n_modes));vel=q.copy()
    out=np.zeros_like(a)
    cc=np.cos(omega*dt);ss=np.sin(omega*dt)
    for j in range(a.shape[1]-1):
        force=a[:,j,None]*coef[None,:]
        qn=q*cc+vel*ss/omega+force*(1-cc)/omega**2
        veln=-q*ss*omega+vel*cc+force*ss/omega
        q,vel=qn,veln
        out[:,j+1]=q@shape
    return out,omega/(2*np.pi)


def read_train_only(A,Y,train):
    """Read only locked development TRAIN rows. Safeguard even if called manually."""
    idx=np.asarray(train,dtype=int)
    if idx.ndim!=1 or len(idx)!=3400 or len(set(idx.tolist()))!=3400 or np.min(idx)<0 or np.max(idx)>=5000:
        raise ValueError('REFUSE_NON_LOCKED_TRAIN_INDICES')
    return np.asarray(A[idx,:],dtype=float),np.asarray(Y[idx,:],dtype=float)


def signs_and_initial_state(A,Y,dt):
    """Descriptive TRAIN-only, does NOT infer absolute polarity or equilibrium truth."""
    if A.shape!=Y.shape or A.ndim!=2 or A.shape[1]<151:
        raise ValueError('INCOMPATIBLE_TRAIN_ARRAYS')
    if not np.isfinite(A).all() or not np.isfinite(Y).all():
        raise ValueError('NONFINITE_TRAIN_VALUES')
    mm=np.asarray(Y,dtype=float)  # raw output is mm
    y=mm*0.001                 # SI metres
    slope=(y[:,1]-y[:,0])/dt
    init={'n_train':A.shape[0], 'time_step_s':dt,
       'elevation_first_sample_abs_p50_mm':float(np.median(np.abs(mm[:,0]))),
       'elevation_first_sample_abs_p95_mm':float(np.percentile(np.abs(mm[:,0]),95)),
       'height_first_difference_rate_abs_p50_m_s':float(np.median(np.abs(slope))),
       'height_first_difference_rate_abs_p95_m_s':float(np.percentile(np.abs(slope),95)),
       'first_input_accel_abs_p50_m_s2':float(np.median(np.abs(A[:,0]))),
       'first_input_accel_abs_p95_m_s2':float(np.percentile(np.abs(A[:,0]),95)),
       'status':'DESCRIPTIVE_NOT_PROOF_OF_REST'}
    preview={}
    for steps in (25,75,125):  # at 0.1, 0.3 and 0.5 s from sequence start
        base,_=model_from_rest(A[:,:steps+1],dt)
        obs=y[:,:steps+1]
        errs={}
        for sign in (-1,1):
            errs[str(sign)]={'from_rest_path_rmse_mm':float(1e3*np.sqrt(np.mean((sign*base[:,1:]-obs[:,1:])**2))),
                'from_rest_endpoint_rmse_mm':float(1e3*np.sqrt(np.mean((sign*base[:,-1]-obs[:,-1])**2)))}
        preview[str(steps*dt)]={'time_horizon_s':steps*dt,
            'relative_polarity_hypotheses':errs,
            'status':'TRAIN_ONLY_EXPLORATORY_ZERO_INITIAL_STATE_ASSUMPTION'}
    return init,preview


def run(root,output,geometry):
    output.mkdir(parents=True,exist_ok=True)
    state={'tool':'F005_E0_Provenance_Audit_v0.5.0_p1','timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'status':'E0_REVIEW_NOT_CERTIFIED','sources_not_modified':True,
       'test_ood_response_access':False,'original_v050_geometry_modified':False,
       'evidence_scope':'CAMILOTTO_THESIS_PLUS_TRAIN_ONLY_DIAGNOSTIC',
       'gates':{'E0_GEOMETRY_DIMENSIONS':'SOURCE_DOCUMENTED',
         'E0_ACCELERATION_AXIS_POLARITY':'BLOCKED_RAW_ARRAY_PROVENANCE',
         'E0_HEIGHT_AXIS_POLARITY':'BLOCKED_RAW_ARRAY_PROVENANCE',
         'E0_INITIAL_EQUILIBRIUM':'BLOCKED_PER_TRAJECTORY',
         'E0_PROVENANCE_ATTESTATION':'BLOCKED','E2_SOURCE_ARRAYS':'NOT_RUN',
         'E3_FROM_REST':'NOT_RUN','E5_EULER_VALIDATION':'NOT_RUN','E7_PKLSA':'NOT_RUN'}}
    try:
        config=json.loads(geometry.read_text(encoding='utf-8'))
        comp,missing,flags=geometry_documentation_check(config)
        state['documented_parameters']=comp
        state['missing_or_invalid_polarity_fields']=missing
        state['unattested_flags']=flags
        if not all(q['match'] for q in comp.values()):
            raise ValueError('THESIS_GEOMETRY_MISMATCH_WITH_LOCKED_V050_CONFIG')
        split=root/'outputs/f005_family_disjoint_v0.4.3/proxy_family_development_split.csv'
        train=load_locked_train_split(split)
        inp=root/'outputs/data_preflight_v0.1.0/data/robot_sloshing/raw_extracted/INPUT_TRAIN.npy'
        out=root/'outputs/data_preflight_v0.1.0/data/robot_sloshing/raw_extracted/OUTPUT_TRAIN.npy'
        if not inp.exists() or not out.exists():
            raise FileNotFoundError('MISSING_ROBOT_NPY_SOURCE')
        if hash_file(inp)!=EXPECTED_INPUT_SHA256:
            raise ValueError('INPUT_SOURCE_SHA256_LOCK_CHANGED')
        AA=np.load(inp,mmap_mode='r'); YY=np.load(out,mmap_mode='r')
        if AA.shape!=(9822,1500) or YY.shape!=(9822,1500):
            raise ValueError('EXPECTED_ROBOT_SHAPES_CHANGED')
        # CRITICAL: read only previously locked DEV_TRAIN response rows.
        A,Y=read_train_only(AA,YY,train)
        init,relative=signs_and_initial_state(A,Y,0.004)
        state['gates']['E2_SOURCE_ARRAYS']='PASS_TRAIN_ONLY_3400_ROWS_LOCKED_SHA256_INPUT'
        state['initial_state_diagnostic']=init
        state['relative_polarity_train_only']=relative
        state['warning']='Only the product of acceleration_axis_sign and measurement_height_sign is observable from this scalar input/output pairing; relative-polarity RMSE is a TRAIN-only data diagnostic, not an independent provenance check. No automatic selection or mutation is performed.'
    except Exception as e:
        state['status']='E0_DIAGNOSTIC_BLOCKED'
        state['blocker']=f'{type(e).__name__}: {e}'
    (output/'e0_audit_report.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    lines=['# F005 v0.5.0 — E0 polarity & provenance audit','',
       '**Status:** '+state['status'], '',
       'Geometry: L=0.080 m, width=0.031 m, h=0.043 m, rho=998 kg/m³ (thesis model), x=+0.040 m. Surface tension set to zero as MODEL ASSUMPTION.','',
       '## Gates']+[f'- {k}: `{v}`' for k,v in state['gates'].items()]+['',
       '## Diagnostic rules',
       '- `+` versus `-` relative polarity is explored only on locked TRAIN input/output arrays; there is **no automatic winner** or geometry-config write.',
       '- Scalar input/output determines a *relative* sign, not both physical axis conventions separately.',
       '- The thesis documents pre-motion baseline subtraction and an analytical zero-state assumption, but does not establish rest for each truncated exported NPY row.',
       '- TEST/OOD responses and development VALIDATION responses are never indexed.',
       '- To unblock E0, inspect the publisher raw-axis mapping AND raw experiment start-state evidence; document both and then amend configuration by explicit human review.',
       '']
    if state.get('initial_state_diagnostic'):
       lines+=['## TRAIN-only starting-state diagnostics','']+[f'- {k}: {v}' for k,v in state['initial_state_diagnostic'].items()]+['']
    if state.get('relative_polarity_train_only'):
       lines+=['## TRAIN-only relative sign (not certified)','']
       for t,entry in state['relative_polarity_train_only'].items():
           lines.append(f"- Horizon {t} s: + RMSE {entry['relative_polarity_hypotheses']['1']['from_rest_path_rmse_mm']:.6g} mm; - RMSE {entry['relative_polarity_hypotheses']['-1']['from_rest_path_rmse_mm']:.6g} mm")
    if state.get('blocker'):lines+=['','## Blocker',state['blocker']]
    (output/'E0_AUDIT_SUMMARY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return state


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ap.add_argument('--geometry',default='config/EULER_GEOMETRY_REQUIRED.json')
    ap.add_argument('--output',default='outputs/f005_e0_provenance_audit_v0.5.0_p1')
    args=ap.parse_args(argv)
    root=Path(args.root).resolve()
    state=run(root,root/args.output,root/args.geometry)
    print(json.dumps({'status':state['status'],'blocker':state.get('blocker','None'),'output':args.output}))
    return 0 if state['status']=='E0_REVIEW_NOT_CERTIFIED' else 2

if __name__=='__main__':sys.exit(main())
