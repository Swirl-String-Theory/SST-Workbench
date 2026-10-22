#!/usr/bin/env python3
"""F005 v0.5.0-p3: conditional linear potential-Euler DEVELOPMENT only.

Uses source-documented flask geometry, locked 0.4.3 proxy split and a TRAIN-selected
relative-polarity hypothesis +1 IN MEMORY. Never changes E0 and never reads TEST/OOD
water heights. Does not assert hydrodynamic rest or identify eight initial modal states
from two scalar height observations.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

THIS=Path(__file__).resolve().parent
sys.path.insert(0,str(THIS))
from f005_euler_v050 import coefficients, simulate, load_split, sha256, EXPECTED_INPUT_SHA256

VERSION='0.5.0-p3'
GEOM_SHA='91f6c876a1ae215dc5bce6c70ce6f192aeb667b9c4e2397d102c53271dca0793'
METRIC_SHA='024af63a4319a5159b40fb11ed33d83afb72195a5ac43647f8c060efd4b27af5'
P2_REQUIRED_GATES={'P2_INPUT_AXIS':'BLOCKED_SOURCE_SEMANTICS',
                   'P2_HEIGHT_AXIS':'BLOCKED_SOURCE_SEMANTICS',
                   'P2_PREMOTION_RAW':'BLOCKED_NO_PER_TRAJECTORY_PROOF'}
ANCHORS=(.004,1.5,2.8)
HORIZONS=(.1,.5,1.,2.,3.)
DT=.004
SIGN_HYPOTHESIS=1  # TRAIN-only relative sign from p1; NOT the two physical axis signs
WALL_DISPLACEMENT_PERTURBATION_M=0.00025  # explicitly arbitrary scenario, not measured uncertainty
WALL_VELOCITY_PERTURBATION_M_S=0.005  # explicitly arbitrary scenario, not measured uncertainty


def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write_json(path,data):Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def geometry_development(g):
    # Independently matched to Camilotto Table 1.1 and Table 2.1, and p2 source audit.
    required={'tank_length_internal_m':.080,'tank_width_internal_m':.031,
      'fill_depth_m':.043,'sensor_x_from_center_m':.040,
      'liquid_density_kg_m3':998.,'surface_tension_N_m':0.,
      'gravity_m_s2':9.81,'n_modes':4}
    for k,x in required.items():
        if k not in g or not np.isfinite(g[k]) or abs(float(g[k])-x)>1e-11:
            raise ValueError('GEOMETRY_MISMATCH:'+k)
    if g.get('initial_equilibrium_confirmed') is True or g.get('provenance_confirmed') is True:
        raise ValueError('P3_EXPECTS_UNATTESTED_E0; NO AUTOMATIC_E0_PROMOTION')
    if g.get('acceleration_axis_sign') is not None or g.get('measurement_height_sign') is not None:
        raise ValueError('P3_REQUIRES_ABSOLUTE_SIGNS_UNRESOLVED')
    if g.get('assumption_2d_longitudinal') is not True:raise ValueError('TWO_DIMENSIONAL_APPROXIMATION_NOT_ENABLED')
    return coefficients(g['tank_length_internal_m'],g['fill_depth_m'],g['sensor_x_from_center_m'],g['liquid_density_kg_m3'],g['surface_tension_N_m'],g['gravity_m_s2'],4)

def audit_p2(j):
    assert j['status']=='E0_P2_REVIEW_NOT_CERTIFIED','P2_STATUS_CHANGED'
    assert j['locked_split']['status']=='LOCKED_INPUT_ONLY_SPLIT_VERIFIED','P2_SPLIT_CHANGED'
    for key,value in P2_REQUIRED_GATES.items():
        assert j['gates'][key]==value,'P2_GATE_CHANGED:'+key
    assert j['gates']['E0_MAIN_EULER_GATE']=='BLOCKED','E0_PROMOTED_OUTSIDE_P3'
    assert j['gates'].get('P2_HYDRODYNAMIC_REST')=='BLOCKED_NOT_OBSERVABLE_FROM_SCALAR_TRACE','HYDRODYNAMIC_REST_GATE_CHANGED'

def score(pred,obs):
    pred=np.asarray(pred); obs=np.asarray(obs)
    if pred.shape!=obs.shape or pred.size<1 or not np.isfinite(pred).all() or not np.isfinite(obs).all():
        raise ValueError('BAD_SCORING_ARRAYS')
    return (float(np.sqrt(np.mean((pred-obs)**2))*1000),
            float(np.sqrt(np.mean((pred[:,-1]-obs[:,-1])**2))*1000))

def seed_modes_two_heights(prev_y_m,at_y_m,prev_accel_m_s2,co,dt=DT,
                           high_q=None,high_v=None):
    """Four-mode family of exact two-observation seed states (in chosen relative coordinates).

    Inverting the exact ZOH propagator over preceding interval makes both sampled
    heights exactly agree for any specified six high-mode q/v values. No claim that
    the resulting state represents the unmeasured true 3D hydrodynamic state.
    """
    _,w,shape,force=co;n=len(w)
    yp=np.atleast_1d(np.asarray(prev_y_m,dtype=float));ya=np.atleast_1d(np.asarray(at_y_m,dtype=float))
    aa=np.atleast_1d(np.asarray(prev_accel_m_s2,dtype=float))
    if yp.shape!=ya.shape or yp.shape!=aa.shape:raise ValueError('SEED_SHAPE_MISMATCH')
    if abs(shape[0])<1e-12 or abs(math.sin(w[0]*dt))<1e-12:raise ValueError('ILL_CONDITIONED_SEED')
    batch=len(yp)
    q=np.zeros((batch,n));v=np.zeros_like(q)
    if high_q is not None:q[:,1:]=np.broadcast_to(high_q,(batch,n-1))
    if high_v is not None:v[:,1:]=np.broadcast_to(high_v,(batch,n-1))
    q[:,0]=(ya-np.sum(q[:,1:]*shape[1:],axis=1))/shape[0]
    c=np.cos(w*dt);s=np.sin(w*dt)
    forcing=aa[:,None]*force[None,:]
    prior_other=np.sum(shape[None,1:]*(c[None,1:]*q[:,1:]
                    -s[None,1:]/w[None,1:]*v[:,1:]
                    +(1-c[None,1:])/w[None,1:]**2*forcing[:,1:]),axis=1)
    prior_zero=shape[0]*(c[0]*q[:,0]+(1-c[0])/w[0]**2*forcing[:,0])
    v[:,0]=(prior_zero+prior_other-yp)/(shape[0]*s[0]/w[0])
    return q,v

def past_observed_height(q,v,prior_a,co,dt=DT):
    _,w,shape,force=co;c=np.cos(w*dt);s=np.sin(w*dt)
    prevq=c[None,:]*q-s[None,:]/w[None,:]*v+(1-c[None,:])/w[None,:]**2*force[None,:]*np.asarray(prior_a)[:,None]
    return prevq@shape

def scenarios(co):
    """13 predefined states: base, +/-0.25 mm and +/-5 mm/s in each high wall mode."""
    shape=co[2]
    yield ('MINIMUM_HIGH_MODES_ZERO',np.zeros(3),np.zeros(3))
    for mod in (1,2,3):
        for typ,mag in (('QWALL',WALL_DISPLACEMENT_PERTURBATION_M),('VWALL',WALL_VELOCITY_PERTURBATION_M_S)):
            for sgn in (-1,1):
                q=np.zeros(3);v=np.zeros(3)
                if typ=='QWALL':q[mod-1]=sgn*mag/shape[mod]
                else:v[mod-1]=sgn*mag/shape[mod]
                yield (f'MODE{mod}_{typ}_{sgn:+d}',q,v)

def homogeneous_delta(time,co,qdelta,vdelta):
    w=co[1];sh=co[2];T=np.asarray(time,dtype=float)[:,None]
    return np.sum(sh[None,:]*(np.cos(T*w[None,:])*qdelta[None,:]
                   +np.sin(T*w[None,:])/w[None,:]*vdelta[None,:]),axis=1)

def csvout(path,rows):
    if not rows:raise ValueError('EMPTY_CSV')
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def historic_metrics(path):
    if not Path(path).is_file() or sha256(path)!=METRIC_SHA:
        raise ValueError('FROZEN_V043_AGGREGATES_MISSING_OR_MODIFIED')
    with Path(path).open(newline='',encoding='utf-8') as f: data=list(csv.DictReader(f))
    if len(data)!=15:raise ValueError('HISTORIC_METRICS_ROW_COUNT')
    keys={(round(float(r['anchor_s']),3),round(float(r['horizon_s']),3)):r for r in data}
    if len(keys)!=15:raise ValueError('HISTORIC_METRICS_KEYS')
    return keys

def locked_arrays(root):
    split=root/'outputs/f005_family_disjoint_v0.4.3/proxy_family_development_split.csv'
    tr,va,audit=load_split(split)
    if not va or max(va)>=5000:raise ValueError('VALIDATION_INDICES_UNSAFE')
    folder=root/'outputs/data_preflight_v0.1.0/data/robot_sloshing/raw_extracted'
    ip=folder/'INPUT_TRAIN.npy';op=folder/'OUTPUT_TRAIN.npy'
    if sha256(ip)!=EXPECTED_INPUT_SHA256:raise ValueError('LOCKED_ACCELERATION_SOURCE_CHANGED')
    X=np.load(ip,mmap_mode='r');Y=np.load(op,mmap_mode='r')
    if X.shape!=(9822,1500) or Y.shape!=(9822,1500):raise ValueError('SOURCE_SHAPES_WRONG')
    idx=np.array(va,dtype=np.int64)
    # CRITICAL: never materialize/read Y except the already-verified DEV_VALIDATION indices.
    accel=np.asarray(X[idx,:],dtype=float)
    obs=np.asarray(Y[idx,:],dtype=float)*.001
    if not np.isfinite(accel).all() or not np.isfinite(obs).all():raise ValueError('NONFINITE_DEV_DATA')
    return accel,obs,audit,idx

def evaluate(accel,obs,co,historic,output):
    """All actual physical parameters fixed; only 850 development-validation rows scored."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    n,nt=accel.shape
    if obs.shape!=(n,nt) or nt!=1500:raise ValueError('DEVELOPMENT_ARRAY_DIMENSIONS')
    if n<1 or not np.isfinite(accel).all() or not np.isfinite(obs).all():raise ValueError('NAN')
    # Primary development: start from assumed rest, no observed height until scoring.
    zero=simulate(accel,DT,co,acceleration_sign=SIGN_HYPOTHESIS)
    oneco=tuple(x[:1] for x in co)
    zero_results=[];cond_results=[];sens_results=[];trace=[]
    for anchor in ANCHORS:
        i=int(round(anchor/DT))
        yprev=obs[:,i-1];yat=obs[:,i];ain=accel[:,i-1]
        q0,v0=seed_modes_two_heights(yprev,yat,ain,co)
        condition=simulate(accel[:,i:],DT,co,q0=q0,v0=v0,acceleration_sign=SIGN_HYPOTHESIS)
        qo,vo=seed_modes_two_heights(yprev,yat,ain,oneco)
        one=simulate(accel[:,i:],DT,oneco,q0=qo,v0=vo,acceleration_sign=SIGN_HYPOTHESIS)
        # Confirm two exact, measured inputs compatible even with previous forcing.
        if not np.allclose(q0@co[2],yat,atol=3e-12,rtol=0):raise ValueError('SEED_AT_MISMATCH')
        if not np.allclose(past_observed_height(q0,v0,ain,co),yprev,atol=3e-12,rtol=0):raise ValueError('SEED_PREVIOUS_MISMATCH')
        # Predefine all initial-state variations, no fitting to validation response.
        shifts=[]
        for name,hq,hv in scenarios(co):
            deltaq,deltav=seed_modes_two_heights(np.array([0.]),np.array([0.]),np.array([0.]),co,high_q=hq,high_v=hv)
            sh=homogeneous_delta(np.arange(nt-i)*DT,co,deltaq[0],deltav[0])
            shifts.append((name,sh))
        assert len(shifts)==13
        for horizon in HORIZONS:
            steps=int(round(horizon/DT)); j=i+steps
            if j>=nt:raise ValueError('HORIZON_OUT_OF_RANGE')
            target=obs[:,i+1:j+1]
            ze=zero[:,i+1:j+1]
            cond=condition[:,1:steps+1]
            onc=one[:,1:steps+1]
            aerr,aend=score(ze,target)
            cerr,cend=score(cond,target)
            oerr,oend=score(onc,target)
            zero_results.append({'anchor_s':anchor,'horizon_s':horizon,'n_dev_validation':n,
                'EULER_FOUR_MODE_FROM_ASSUMED_REST_PATH_RMSE_MM':aerr,
                'EULER_FOUR_MODE_FROM_ASSUMED_REST_ENDPOINT_RMSE_MM':aend,
                'claim':'NONBLIND_ASSUMED_ZERO_INITIAL_STATE_NO_HEIGHT_SEED'})
            row={'anchor_s':anchor,'horizon_s':horizon,'n_dev_validation':n,
                'EULER_ONE_MODE_TWO_HEIGHT_PATH_RMSE_MM':oerr,
                'EULER_ONE_MODE_TWO_HEIGHT_ENDPOINT_RMSE_MM':oend,
                'EULER_FOUR_MODE_MINIMUM_SEED_PATH_RMSE_MM':cerr,
                'EULER_FOUR_MODE_MINIMUM_SEED_ENDPOINT_RMSE_MM':cend,
                'initial_state':'TWO_HEIGHTS_PLUS_ASSUMPTION_HIGH_MODES_ZERO'}
            if historic is not None:
                h=historic[(round(anchor,3),round(horizon,3))]
                row['HISTORICAL_ARX_PATH_RMSE_MM']=float(h['ARX_RETRAINED_PATH_RMSE_MM'])
                row['HISTORICAL_OSCILLATOR_PATH_RMSE_MM']=float(h['OSCILLATOR_INDEPENDENT_TRAIN_FIT_PATH_RMSE_MM'])
                row['HISTORICAL_ARX_ENDPOINT_RMSE_MM']=float(h['ARX_RETRAINED_ENDPOINT_RMSE_MM'])
                row['HISTORICAL_OSCILLATOR_ENDPOINT_RMSE_MM']=float(h['OSCILLATOR_INDEPENDENT_TRAIN_FIT_ENDPOINT_RMSE_MM'])
                row['comparison_class']='EXPOSED_DEVELOPMENT_SAME_ANCHOR_HORIZON_DIFFERENT_MODEL_INITIAL_STATE'
            cond_results.append(row)
            for name,sh in shifts:
                alt=cond+sh[None,1:steps+1]
                path,end=score(alt,target)
                sens_results.append({'anchor_s':anchor,'horizon_s':horizon,'scenario':name,
                  'PATH_RMSE_MM':path,'ENDPOINT_RMSE_MM':end,
                  'MAX_ABS_CHANGE_FROM_MINIMUM_SEED_MM':float(np.max(np.abs(sh[1:steps+1]))*1000),
                  'ENDPOINT_CHANGE_FROM_MINIMUM_SEED_MM':float(sh[steps]*1000),
                  'wall_displacement_perturbation_mm':WALL_DISPLACEMENT_PERTURBATION_M*1000,
                  'wall_velocity_perturbation_mm_s':WALL_VELOCITY_PERTURBATION_M_S*1000,
                  'assumed_not_measured':True})
            # Fixed first development validation case, for plot only.
            if abs(anchor-1.5)<1e-9 and horizon==3.:
                for idx in range(0,steps+1,10):
                    trace.append({'time_s':round(anchor+idx*DT,6),
                      'experiment_mm':float(obs[0,i+idx]*1000),
                      'euler_from_rest_mm':float(zero[0,i+idx]*1000),
                      'one_mode_conditional_mm':float(one[0,idx]*1000),
                      'four_mode_minimum_seed_mm':float(condition[0,idx]*1000)})
    csvout(output/'p3_from_rest_metrics.csv',zero_results)
    csvout(output/'p3_conditional_metrics.csv',cond_results)
    csvout(output/'p3_initial_state_sensitivity.csv',sens_results)
    envelopes=[]
    for anchor in ANCHORS:
        for horizon in HORIZONS:
            sr=[r for r in sens_results if r['anchor_s']==anchor and r['horizon_s']==horizon]
            envelopes.append({'anchor_s':anchor,'horizon_s':horizon,'n_scenarios':len(sr),
              'min_scenario_path_rmse_mm':min(z['PATH_RMSE_MM'] for z in sr),
              'max_scenario_path_rmse_mm':max(z['PATH_RMSE_MM'] for z in sr),
              'max_absolute_model_displacement_from_seed_mm':max(z['MAX_ABS_CHANGE_FROM_MINIMUM_SEED_MM'] for z in sr),
              'uncertainty_interpretation':'DETERMINISTIC_SCENARIOS_NOT_CONFIDENCE_LIMITS'})
    csvout(output/'p3_initial_state_envelopes.csv',envelopes)
    csvout(output/'p3_fixed_trace_sample.csv',trace)
    return {'n_validation':n,'from_rest':zero_results,'conditional':cond_results,
      'sensitivity_scenario_count':len(tuple(scenarios(co))),
      'sensitivity_result_rows':len(sens_results),
      'min_seed_is_unique':False,'modal_state_dimension':8,
      'measured_scalar_samples_used_to_initialize':2,
      'higher_mode_wall_displacement_scenario_mm':.25,
      'higher_mode_wall_velocity_scenario_mm_s':5.,
      'reference_comparison':'HISTORICAL_V043_AGGREGATES_NONBLIND_NOT_PROVENANCE_CERTIFIED'}

def make_pdf(path,status,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from textwrap import wrap
    with PdfPages(path) as pdf:
        fig=plt.figure(figsize=(8.27,11.69));fig.patch.set_facecolor('white')
        ypos=[.955]
        def para(message,size=10,bold=False):
            for ln in wrap(str(message),100 if size<=10 else 67):
                fig.text(.08,ypos[0],ln,fontsize=size,fontweight=('bold' if bold else 'normal'),va='top',color='#19324B')
                ypos[0]-=.021 if size<=10 else .035
            ypos[0]-=.012
        para('F005 v0.5.0-p3 | Conditional Euler Development',16,True)
        para('Development only. E0 polarity & hydrodynamic-rest provenance remain BLOCKED.',10,True)
        para('Model: linearized inviscid, incompressible, irrotational 2D Euler potential flow. L=0.080 m, h=0.043 m, four odd modes, sigma=0 model assumption. No fitted frequency, damping or fluid-clock hypothesis.')
        para('Hypotheses / locked scope',12,True)
        para('From-rest uses all q_n(0)=v_n(0)=0; this is assumed, not verified per experiment. In-memory relative sign +1 was selected using TRAIN-only exploratory diagnostic; absolute coordinate signs remain UNKNOWN.')
        para('Conditional modes: two measured wall heights at t0-dt and t0, then known future acceleration but NO measured height feedback. Four modes have eight unknown state components: the extra six are not identifiable from two scalar observations.')
        para('Sensitivity: 13 deterministic state scenarios: minimum seed and +/-0.25 mm wall amplitude or +/-5 mm/s wall velocity in higher modes 1,2,3. These perturbations are arbitrary diagnostics, NOT measurement confidence limits.')
        para('Gates',12,True)
        for key,val in status['gates'].items():para(f'{key}: {val}',9)
        para('No TEST/OOD water heights accessed; original EULER_GEOMETRY_REQUIRED.json left unchanged. v0.4.3 is an exposed development split, NOT a blind family-certified holdout.',9,True)
        pdf.savefig(fig);plt.close(fig)
        if status.get('evaluation'):
            rows=status['evaluation']['conditional']
            xx=np.array(HORIZONS)
            fig,ax=plt.subplots(figsize=(9,5.9));sel=[r for r in rows if r['anchor_s']==1.5]
            for key,name in [('EULER_ONE_MODE_TWO_HEIGHT_PATH_RMSE_MM','One-mode Euler'),('EULER_FOUR_MODE_MINIMUM_SEED_PATH_RMSE_MM','Four-mode min seed'),('HISTORICAL_ARX_PATH_RMSE_MM','v0.4.3 ARX'),('HISTORICAL_OSCILLATOR_PATH_RMSE_MM','v0.4.3 oscillator')]:
                if key in sel[0]:ax.plot(xx,[r[key] for r in sel],marker='o',label=name)
            ax.set(xlabel='Forecast horizon [s]',ylabel='Full-path RMSE [mm]',title='Exposed development: conditional predictions (anchor 1.5 s)')
            ax.legend();ax.grid(alpha=.25);fig.tight_layout();pdf.savefig(fig);plt.close(fig)
            fig,ax=plt.subplots(figsize=(9,5.9))
            with (output/'p3_fixed_trace_sample.csv').open(newline='',encoding='utf-8') as f:
                data=list(csv.DictReader(f))
            for key,name in [('experiment_mm','Experiment'),('one_mode_conditional_mm','One-mode conditional'),('four_mode_minimum_seed_mm','Four-mode min seed'),('euler_from_rest_mm','From assumed rest')]:
                ax.plot([float(z['time_s']) for z in data],[float(z[key]) for z in data],label=name)
            ax.set(xlabel='Time [s]',ylabel='Wall-height [mm]',title='Fixed first development-validation example; no selection by error')
            ax.legend();ax.grid(alpha=.25);fig.tight_layout();pdf.savefig(fig);plt.close(fig)
            parafig=plt.figure(figsize=(8.27,11.69));parafig.patch.set_facecolor('white')
            parafig.text(.08,.94,'Interpreting the results',fontsize=16,weight='bold')
            body=[
              'A low RMSE for an Euler conditional forecast does not certify Euler physics: it uses measured height seeds, unverified axis signs, and a nonblind development pool.',
              'Four-modal initial state is non-unique. The zero-high-mode seed is a modeling choice, not an inference from the two measured heights. Sensitivity ranges are scenario-dependent, not experimental confidence intervals.',
              'Historical v0.4.3 ARX and oscillator scores are supplied only for transparent descriptive comparison at the same anchors/horizons and development population. The ARX/oscillator parameters are never supplied to Euler.',
              'No claims concerning source-native PKLSA, torsional light, Kelvin waves, or SST gravity are established by this test.',
              'References: D. Camilotto (2026), A Comprehensive Data-Driven Framework for Robotic Liquid Sloshing Control, Politecnico di Milano, https://hdl.handle.net/10589/253216.',
              'O. M. Faltinsen and A. N. Timokha (2009), Sloshing, Cambridge University Press, ISBN 9780521881111.',
            ]
            yy=.89
            for item in body:
                for ln in wrap(item,92):
                    parafig.text(.08,yy,ln,fontsize=10,va='top');yy-=.023
                yy-=.029
            pdf.savefig(parafig);plt.close(parafig)

def report_write(output,report):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write_json(output/'p3_report.json',report)
    s=['# F005 v0.5.0-p3 — Conditional Euler Development & Initial-State Sensitivity',
     '',f"**Status:** `{report['status']}`",'',
     '## Gates', '']
    s += [f'- {k}: `{v}`' for k,v in report['gates'].items()]
    s+=['','## Scientific boundaries','',
       '- Relative polarity +1: frozen TRAIN-only hypothesis, not an attested physical axis convention.',
       '- From-rest: ZERO STATE ASSUMPTION, not independently observed hydrodynamic rest.',
       '- Conditional one-mode and four-mode-minimum-seed: two measured heights at anchor; future forcing known.',
       '- Four modes imply eight initial states; two height observations do not uniquely fix them.',
       '- Sensitivity amplitudes are prescribed examples, NOT confidence bounds.',
       '- v0.4.3 is nonblind/proxy family-disjoint; no TEST/OOD output access.',
       '- E0 remains blocked. E7/PKLSA NOT RUN. SST physical claims UNRESOLVED.',
       '',f"## Blocker",str(report.get('blocker','None (development audit still uncertified).')),'']
    if report.get('evaluation'):
        z=report['evaluation'];s += ['## Development numerical outputs','',
            f"- Validation trajectories: {z['n_validation']}",
            f"- Predeclared conditional comparisons: {len(z['conditional'])}",
            f"- Initial-state-sensitivity scenarios: {z['sensitivity_scenario_count']}",
            f"- Sensitivity rows: {z['sensitivity_result_rows']}",'']
    (output/'P3_SUMMARY.md').write_text('\n'.join(s)+'\n',encoding='utf-8')
    try:make_pdf(output/'F005_v0.5.0-p3_LINEAR_EULER_DEVELOPMENT.pdf',report,output)
    except ImportError: (output/'PDF_MISSING_DEPENDENCY.txt').write_text('Install matplotlib\n')

def run(root,out,demo=False):
    root=Path(root);out=Path(out)
    report={'tool':'F005_v0.5.0-p3','generated_utc':datetime.now(timezone.utc).isoformat(),
      'status':'BLOCKED_PENDING_REAL_DEVELOPMENT_DATA',
      'gates':{'E0_GEOMETRY':'SOURCE_DOCUMENTED_E0_POLARITY_AND_REST_BLOCKED',
        'P2_SOURCE_PROVENANCE':'REVIEW_NOT_CERTIFIED','E1_MODAL':'ANALYTIC_REFERENCE',
        'E2_LOCKED_INPUT':'NOT_RUN','E3_FROM_ASSUMED_REST':'NOT_RUN',
        'E4_CONDITIONAL':'NOT_RUN','E4_SENSITIVITY':'NOT_RUN',
        'E5_DESCRIPTIVE_MODEL_COMPARISON':'NOT_RUN',
        'E6_PROXY_FAMILY':'DEVELOPMENT_ONLY','E9_LINEARIZATION':'NOT_RUN','E7_PKLSA':'NOT_RUN',
        'E8_SST_PHYSICS':'UNRESOLVED'},
      'relative_sign_hypothesis_from_train_only':SIGN_HYPOTHESIS,
      'absolute_input_sign':'UNVERIFIED','absolute_output_sign':'UNVERIFIED',
      'e0_original_not_modified':True,'test_ood_water_height_read':False,
      'limitations':['Zero-rest assumed, not documented per trajectory','Potential-Euler not nonlinear Euler',
        'No damping; only axisymmetric? no - longitudinal 2D surface modes',
        'Arbitrary perturbation sizes, not uncertainty intervals']}
    try:
        if demo:
            co=coefficients(.08,.043,.04,998.,0.,9.81,4)
            t=np.arange(1500)*DT
            a=np.vstack([.5*np.sin(2*math.pi*2.5*t)*np.exp(-t) for _ in range(12)])
            y=simulate(a,DT,co)
            # Introduce a nonzero high-mode seed in synthetic observation; no metadata from real data.
            y+=.0002*np.cos(co[1][1]*t)[None,:]
            hist=None
            report['status']='DEMO_SYNTHETIC_NO_EXPERIMENTAL_VALIDATION'
            report['gates']['E2_LOCKED_INPUT']='DEMO_ONLY'
            report['gates']['E6_PROXY_FAMILY']='DEMO_ONLY'
            report['gates']['P2_SOURCE_PROVENANCE']='NOT_APPLICABLE_DEMO'
        else:
            geompath=root/'config/EULER_GEOMETRY_REQUIRED.json'
            if sha256(geompath)!=GEOM_SHA:raise ValueError('GEOMETRY_CONTRACT_HASH_MISMATCH')
            g=read_json(geompath);co=geometry_development(g)
            p2path=root/'outputs/f005_raw_provenance_v0.5.0_p2/p2_audit_report.json'
            p2=read_json(p2path);audit_p2(p2)
            hist=historic_metrics(root/'outputs/f005_family_disjoint_v0.4.3/validation_full_path_metrics.csv')
            a,y,split,idx=locked_arrays(root)
            report['input_provenance']={'geometry_sha256':sha256(geompath),'p2_sha256':sha256(p2path),
                'v043_baseline_metrics_sha256':METRIC_SHA,
                'input_npy_sha256':EXPECTED_INPUT_SHA256,'v043_dev_validation_rows':len(idx),
                'output_npy_full_hash':'NOT_COMPUTED_TEST_OOD_SEALED'}
            report['gates']['E2_LOCKED_INPUT']='PASS_DEV_VALIDATION_ONLY'
            report['gates']['E6_PROXY_FAMILY']='LOCKED_PROXY_SPLIT_NOT_TRUE_FAMILY_CERTIFIED'
        report['analytic_frequencies_hz']=(co[1]/(2*math.pi)).tolist()
        report['maximum_observed_absolute_wall_height_over_depth']=float(np.max(np.abs(y))/.043)
        report['gates']['E9_LINEARIZATION']='REVIEW_AMPLITUDE_OVER_20PCT_DEPTH' if report['maximum_observed_absolute_wall_height_over_depth']>.2 else 'AMPLITUDE_BELOW_20PCT_DEPTH_SLOPES_UNVERIFIED'
        report['evaluation']=evaluate(a,y,co,hist,out)
        report['gates']['E3_FROM_ASSUMED_REST']='DEVELOPMENT_ASSUMPTION_ONLY'
        report['gates']['E4_CONDITIONAL']='DEVELOPMENT_TWO_HEIGHT_SEED_ONLY'
        report['gates']['E4_SENSITIVITY']='SCENARIO_NONIDENTIFIABILITY_DEMONSTRATED'
        report['gates']['E5_DESCRIPTIVE_MODEL_COMPARISON']='DEVELOPMENT_NOT_BLIND' if hist else 'NOT_APPLICABLE_DEMO'
        if not demo:report['status']='DEVELOPMENT_CONDITIONAL_EULER_E0_BLOCKED'
    except Exception as e:
        report['status']='BLOCKED_FAIL_CLOSED';report['blocker']=f'{type(e).__name__}: {e}'
    report_write(out,report)
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--out',default='outputs/f005_conditional_euler_v0.5.0_p3');ap.add_argument('--demo',action='store_true')
    a=ap.parse_args();root=Path(a.root).resolve();out=root/a.out
    r=run(root,out,a.demo)
    print(json.dumps({'status':r['status'],'blocker':r.get('blocker'),'output':str(out)}))
    return 0 if r['status'].startswith(('DEVELOPMENT_','DEMO_')) else 2
if __name__=='__main__':sys.exit(main())
