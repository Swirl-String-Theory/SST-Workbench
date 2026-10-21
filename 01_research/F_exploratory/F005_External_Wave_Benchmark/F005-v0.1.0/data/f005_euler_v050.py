#!/usr/bin/env python3
"""F005 v0.5.0: linearized inviscid Euler free-surface modal baseline.

NO fitted dataset geometry. Source-provenance check fails closed.
TEST/OOD heights are never indexed; use only DEV_VALIDATION source rows.
The label Euler denotes the linearized potential-Euler boundary-value problem,
NOT a full nonlinear Euler or Navier-Stokes CFD solver.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
VERSION='0.5.0'
EXPECTED_SPLIT_SHA256='d60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2'
EXPECTED_INPUT_SHA256='5d51b77ecf20cc4327c11a416e5e70c42a63c8499b8f9ba7c0af1fdc35af3aed'
ANCHORS=(0.004,1.5,2.8)
HORIZONS=(.1,.5,1.,2.,3.)

def sha256(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**21),b''):h.update(b)
 return h.hexdigest()

def validate_geometry(obj):
 """Fail closed on absent measured values, attribution, polarity and fluid conditions."""
 req=('tank_length_internal_m','tank_width_internal_m','fill_depth_m','sensor_x_from_center_m','liquid_density_kg_m3','surface_tension_N_m','acceleration_axis_sign','measurement_height_sign','geometry_source','sensor_source','orientation_source','fluid_source','initial_equilibrium_source')
 missing=[k for k in req if obj.get(k) is None or obj.get(k)=='' ]
 if missing: raise ValueError('GEOMETRY_UNVERIFIED: missing '+', '.join(missing))
 if obj.get('evidence_class') not in ('PUBLISHER_DOCUMENTED','DIRECTLY_MEASURED_WITH_RECORD'):
  raise ValueError('GEOMETRY_UNVERIFIED: evidence_class needs source or measurement record')
 if obj.get('provenance_confirmed') is not True:
  raise ValueError('GEOMETRY_UNVERIFIED: provenance_confirmed must be true, not guessed')
 L=float(obj['tank_length_internal_m']); B=float(obj['tank_width_internal_m']);h=float(obj['fill_depth_m']);x=float(obj['sensor_x_from_center_m'])
 rho=float(obj['liquid_density_kg_m3']); sig=float(obj['surface_tension_N_m'])
 if not (0<L<2 and 0<B<2 and 0<h<1 and abs(x)<=L/2+1e-10 and rho>0 and sig>=0):raise ValueError('INVALID_GEOMETRY_OR_UNITS')
 if obj['acceleration_axis_sign'] not in (-1,1) or obj['measurement_height_sign'] not in (-1,1):raise ValueError('INVALID_POLARITY')
 if obj.get('assumption_2d_longitudinal') is not True:raise ValueError('BLOCKED_2D_ASSUMPTION_NOT_ATTESTED')
 if obj.get('initial_equilibrium_confirmed') is not True:raise ValueError('BLOCKED_INITIAL_EQUILIBRIUM_UNVERIFIED')
 if obj.get('sensor_quantity')!='absolute_free_surface_elevation_relative_to_static_level':raise ValueError('SENSOR_MEASURAND_NOT_CONFIRMED')
 if not(0<float(obj.get('gravity_m_s2',0))<20):raise ValueError('GRAVITY_NOT_SPECIFIED')
 return obj

def coefficients(L,h,x,rho,sig,g,nmodes):
 """Physical modal coefficients of linear potential Euler for longitudinal forcing.

 eta(x,t) = sum q_n(t) sin(k_n*x) ; k_n=(2n+1)pi/L
 q''+omega_n² q = -k_n*tanh(k_n h)*b_n*a(t)
 b_n=4 (-1)^n /(L*k_n²), from expansion x=sum b_n sin(k_n*x)
 No wall displacement, flat bottom, inviscid, irrotational, small slopes.
 """
 n=np.arange(int(nmodes));k=(2*n+1)*math.pi/L
 w2=(g*k+(sig/rho)*k**3)*np.tanh(k*h)
 shape=np.sin(k*x)
 b=4*(-1.)**n/(L*k*k)
 force=-k*np.tanh(k*h)*b
 return k,np.sqrt(w2),shape,force

def simulate(a,dt,coeff,*,q0=None,v0=None,acceleration_sign=1,measurement_sign=1):
 """Exact piecewise-constant-force recurrence, linear Euler modes.

 Input a is m/s^2: shape (number trajectories, number time samples).
 Output eta has m; no empirical fit. a[:,j] acts over [t_j,t_{j+1}).
 """
 a=np.asarray(a,dtype=float)
 if a.ndim!=2 or not np.isfinite(a).all(): raise ValueError('Invalid acceleration input')
 k,w,shape,force=coeff
 nrow,nt=a.shape; nmode=len(w)
 q=np.zeros((nrow,nmode)) if q0 is None else np.asarray(q0,float).copy()
 v=np.zeros((nrow,nmode)) if v0 is None else np.asarray(v0,float).copy()
 if q.shape!=(nrow,nmode) or v.shape!=q.shape: raise ValueError('modal initial condition shape')
 c=np.cos(w*dt)[None,:];s=np.sin(w*dt)[None,:];om=w[None,:];f=force[None,:]
 result=np.zeros((nrow,nt),dtype=float)
 result[:,0]=measurement_sign*(q @ shape)
 for j in range(nt-1):
  F=f * (acceleration_sign * a[:,j:j+1])
  q_new=c*q + s/om*v + (1-c)/om**2*F
  v_new=-om*s*q+c*v+s/om*F
  q,v=q_new,v_new
  result[:,j+1]=measurement_sign*(q@shape)
 return result

def initial_condition_one_mode(eta_prev_mm,eta_at_mm,dt,shape,measurement_sign):
 """One-mode conditional forecast uses precisely two measured initial heights."""
 if len(shape)!=1 or abs(shape[0])<1e-9:raise ValueError('ONE_MODE_IDENTIFICATION_ONLY')
 z0=np.asarray(eta_at_mm,dtype=float)*1e-3/measurement_sign
 zm=np.asarray(eta_prev_mm,dtype=float)*1e-3/measurement_sign
 q=(z0/shape[0])[:,None]
 v=((z0-zm)/dt/shape[0])[:,None]
 return q,v

def load_split(p):
 if sha256(p)!=EXPECTED_SPLIT_SHA256:raise ValueError('LOCKED_SPLIT_HASH_MISMATCH')
 rows=[]
 with Path(p).open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):rows.append((int(r['row_id_zero_based']),r['partition'],r['proxy_component_id']))
 if len(rows)!=4250 or len({x[0] for x in rows})!=4250:raise ValueError('SPLIT_POPULATION_MISMATCH')
 groups={}
 for idx,p,g in rows:
  if not 0<=idx<5000 or p not in ('DEV_TRAIN','DEV_VALIDATION'):raise ValueError('LOCKED_TEST_OOD_MEMBERSHIP')
  groups.setdefault(g,set()).add(p)
 if any(len(v)>1 for v in groups.values()):raise ValueError('PROXY_GROUP_LEAKAGE')
 tr=[i for i,p,g in rows if p=='DEV_TRAIN'];va=[i for i,p,g in rows if p=='DEV_VALIDATION']
 if len(tr)!=3400 or len(va)!=850:raise ValueError('SPLIT_COUNTS_CHANGED')
 return tr,va,{'population':4250,'train':len(tr),'validation':len(va),'proxy_components':len(groups),'cross_split_components':0}

def metrics(pred,exp):
 pred=np.asarray(pred);exp=np.asarray(exp)
 if pred.shape!=exp.shape or pred.size==0 or not np.isfinite(pred).all() or not np.isfinite(exp).all():raise ValueError('bad metrics input')
 return float(np.sqrt(np.mean((pred-exp)**2))*1000)

def report_pdf(path,state,curves=None,model=None):
 from matplotlib.backends.backend_pdf import PdfPages
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from textwrap import wrap
 with PdfPages(path) as pdf:
  fig=plt.figure(figsize=(8.27,11.69));fig.patch.set_facecolor('white');fig.subplots_adjust(0,0,1,1)
  x,y=.08,.96
  def line(t,fontsize=10,bold=False,col='#18283B'):
   nonlocal y
   for ln in wrap(str(t),103):
    fig.text(x,y,ln,fontsize=fontsize,fontweight=('bold' if bold else 'normal'),color=col,fontfamily='DejaVu Sans',va='top');y-=.023 if fontsize<=11 else .037
   y-=.010
  line('F005 v0.5.0 - INDEPENDENT LINEARIZED EULER SLOSHING',15,True)
  line('Evidence-first / no fitted frequency / no damping fit / not nonlinear Euler',10)
  line('Status: '+state['scientific_status'],11,True,col='#9B4226' if 'BLOCKED' in state['scientific_status'] else '#175C65')
  line('Source and model boundary',12,True)
  line('Potential flow linearized around still water, rectangular 2D tank, impermeable rigid walls/bottom, small free-surface displacement.')
  line('k_n = (2n+1)pi/L; omega_n^2 = (g*k_n + sigma*k_n^3/rho) * tanh(k_n*h)')
  line('q_n" + omega_n^2*q_n = -k_n*tanh(k_n*h)*b_n*a(t)')
  line('b_n=4(-1)^n/(L k_n^2), eta(x,t)=sum_n q_n(t)sin(k_n x).')
  line('Forcing uses publisher acceleration. Zero damping is enforced as inviscid Euler; friction/contact/meniscus/3D flow remain unmodelled.')
  line('Gates',12,True)
  for a,b in state['gates'].items():line(a+': '+str(b))
  line('Inputs and provenance',12,True)
  for z in state.get('notes',[]):line('- '+z)
  line('Do NOT promote: physical SST and source-native PKLSA remain UNRESOLVED.',10,True)
  pdf.savefig(fig);plt.close(fig)
  if curves is not None:
   fig,ax=plt.subplots(figsize=(8.27,5.8));time,obs,yEuler=curves
   ax.plot(time,obs*1000,label='Experiment',lw=1);ax.plot(time,yEuler*1000,label='Euler geometry-only',lw=1)
   ax.set(xlabel='Time [s]',ylabel='Free surface [mm]',title='Predesignated validation example (not optimized)');ax.legend();ax.grid(alpha=.3)
   fig.tight_layout();pdf.savefig(fig);plt.close(fig)

def run(root,geometry,output,*,demo=False):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 status={'tool':'F005_Independent_Linear_Euler_v0.5.0','utc':datetime.now(timezone.utc).isoformat(),
  'scientific_status':'BLOCKED_GEOMETRY_UNVERIFIED',
  'gates':{'E0_GEOMETRY':'BLOCKED','E1_MODAL_SOLVER':'PASS_ANALYTIC_TESTS_REQUIRED','E2_INPUT_INTEGRITY':'NOT_RUN','E3_FROM_REST':'NOT_RUN','E4_CONDITIONAL_ONE_MODE':'NOT_RUN','E5_BASELINE_COMPARISON':'NOT_RUN','E6_FAMILY_DISJOINT':'DEVELOPMENT_PROXY_ONLY','E7_PKLSA':'NOT_RUN','E8_SST_CLAIMS':'UNRESOLVED','E9_LINEARIZATION':'NOT_RUN'},
  'notes':['0.4.3 unchanged; frozen TEST/OOD response signals not indexed.','Geometry cannot be inferred from T75 designation or prior ARX/oscillator fitted frequency.','Without verified dimensions and sensor polarity, no physical forecast is reported.']}
 curves=None
 try:
  if demo:
   G={'tank_length_internal_m':.12,'tank_width_internal_m':.06,'fill_depth_m':.020,'sensor_x_from_center_m':.060,'liquid_density_kg_m3':998.,'surface_tension_N_m':0.,'gravity_m_s2':9.81,'acceleration_axis_sign':1,'measurement_height_sign':1,'geometry_source':'SYNTHETIC_DEMO','sensor_source':'SYNTHETIC_DEMO','orientation_source':'SYNTHETIC_DEMO','fluid_source':'SYNTHETIC_DEMO','initial_equilibrium_source':'SYNTHETIC_DEMO','initial_equilibrium_confirmed':True,'evidence_class':'DIRECTLY_MEASURED_WITH_RECORD','provenance_confirmed':True,'assumption_2d_longitudinal':True,'sensor_quantity':'absolute_free_surface_elevation_relative_to_static_level','n_modes':5}
   t=np.arange(1500)*.004;a=(np.exp(-((t-.5)/.15)**2))[None,:]
   co=coefficients(G['tank_length_internal_m'],G['fill_depth_m'],G['sensor_x_from_center_m'],G['liquid_density_kg_m3'],G['surface_tension_N_m'],G['gravity_m_s2'],5)
   yy=simulate(a,.004,co)[0];curves=t,yy,yy
   status['scientific_status']='DEMO_SYNTHETIC_NOT_EXPERIMENT';status['gates']['E0_GEOMETRY']='DEMO_ONLY';status['gates']['E1_MODAL_SOLVER']='PASS_SYNTHETIC';status['gates']['E2_INPUT_INTEGRITY']='SYNTHETIC';status['notes'].append('ALL values are deliberately hypothetical; this output cannot validate the Zenodo experiment.')
  else:
   try:G=validate_geometry(json.loads(Path(geometry).read_text(encoding='utf8')))
   except (ValueError,FileNotFoundError,json.JSONDecodeError) as e:
    status['blocker']=str(e);return write(status,output,curves)
   status['gates']['E0_GEOMETRY']='PASS_USER_ATTESTED_NOT_INDEPENDENTLY_REVIEWED'
   path=root/'outputs'/'f005_family_disjoint_v0.4.3'/'proxy_family_development_split.csv'
   if not path.exists():status['blocker']='MISSING_V043_SPLIT';return write(status,output,curves)
   _,va,si=load_split(path)
   status['split']=si;status['gates']['E6_FAMILY_DISJOINT']='PASS_PROXY_GRAPH_ONLY_NOT_TRUE_FAMILY'
   inp=root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'/'INPUT_TRAIN.npy'
   out=root/'outputs'/'data_preflight_v0.1.0'/'data'/'robot_sloshing'/'raw_extracted'/'OUTPUT_TRAIN.npy'
   if not inp.exists() or not out.exists():status['blocker']='MISSING_NPY_SOURCE';return write(status,output,curves)
   if sha256(inp)!=EXPECTED_INPUT_SHA256:status['blocker']='SOURCE_ACCELERATION_HASH_MISMATCH';return write(status,output,curves)
   status['gates']['E2_INPUT_INTEGRITY']='PASS_LOCKED_SHA256'
   # Deliberately ONLY index the 850 development validation rows. No TEST/OOD labels permitted.
   A=np.load(inp,mmap_mode='r');Y=np.load(out,mmap_mode='r')
   if A.shape!=(9822,1500) or Y.shape!=(9822,1500):status['blocker']='DATA_SHAPES_CHANGED';return write(status,output,curves)
   v=np.asarray(va,dtype=int)
   accel=np.asarray(A[v,:],dtype=float)
   y=np.asarray(Y[v,:],dtype=float)*.001
   if not np.isfinite(accel).all() or not np.isfinite(y).all():status['blocker']='NONFINITE_DEVELOPMENT_DATA';return write(status,output,curves)
   dt=.004
   nm=int(G.get('n_modes',5));
   if nm<1 or nm>17:status['blocker']='INVALID_MODE_COUNT';return write(status,output,curves)
   args=(G['tank_length_internal_m'],G['fill_depth_m'],G['sensor_x_from_center_m'],G['liquid_density_kg_m3'],G['surface_tension_N_m'],G['gravity_m_s2'])
   co=coefficients(*map(float,args),nm)
   out_euler=simulate(accel,dt,co,acceleration_sign=G['acceleration_axis_sign'],measurement_sign=G['measurement_height_sign'])
   status['modal_frequencies_hz']=(co[1]/(2*math.pi)).tolist()
   status['geometry']=G;status['gates']['E1_MODAL_SOLVER']='PASS_EXACT_ZOH_MODAL';status['gates']['E3_FROM_REST']='DEVELOPMENT_EVALUATED'
   rows=[]
   # Independent from rest: compare at the same fixed anchoring windows as v0.4.3, no measured initialization.
   for anchor in ANCHORS:
    for horizon in HORIZONS:
     i=int(round(anchor/dt));j=i+int(round(horizon/dt));
     if j>=accel.shape[1]:raise ValueError('Window extends beyond raw data')
     observed=y[:,i+1:j+1];pr=out_euler[:,i+1:j+1]
     rows.append({'anchor_s':anchor,'horizon_s':horizon,'number_of_trajectories':len(v),'num_steps':j-i,
       'EULER_FROM_REST_PATH_RMSE_MM':metrics(pr,observed),'EULER_FROM_REST_ENDPOINT_RMSE_MM':metrics(pr[:,-1:],observed[:,-1:]),
       'initial_condition':'ZERO_AT_START_NO_MEASURED_HEIGHT','comparison_scope':'NOT_LIKE_FOR_LIKE_WITH_V043_TWO_MEASURED_HEIGHT_SEEDS'})
   with (output/'euler_geometry_only_metrics.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
   status['geometry_only_forecasts']=rows
   ratio=float(np.max(np.abs(y))/float(G['fill_depth_m']))
   status['max_observed_eta_over_depth']=ratio
   status['gates']['E9_LINEARIZATION']=('REVIEW_LARGE_AMPLITUDE_OVER_20_PERCENT_DEPTH' if ratio>0.2 else 'AMPLITUDE_CHECK_BELOW_20_PERCENT_DEPTH_SLOPE_UNVERIFIED')
   # Physically constrained one-mode conditional initialization: two heights, no measurements afterwards.
   co1=coefficients(*map(float,args),1)
   cond=[]
   for anchor in ANCHORS:
    j=int(round(anchor/dt))
    q,vv=initial_condition_one_mode(y[:,j-1]*1000,y[:,j]*1000,dt,co1[2],G['measurement_height_sign'])
    pred=simulate(accel[:,j:],dt,co1,q0=q,v0=vv,acceleration_sign=G['acceleration_axis_sign'],measurement_sign=G['measurement_height_sign'])
    for horizon in HORIZONS:
     steps=int(round(horizon/dt))
     obs=y[:,j+1:j+steps+1];p=pred[:,1:steps+1]
     cond.append({'anchor_s':anchor,'horizon_s':horizon,'number_of_trajectories':len(v),'num_steps':steps,
      'EULER_ONE_MODE_CONDITIONAL_PATH_RMSE_MM':metrics(p,obs),'EULER_ONE_MODE_CONDITIONAL_ENDPOINT_RMSE_MM':metrics(p[:,-1:],obs[:,-1:]),
      'initial_condition':'TWO_OBSERVED_HEIGHTS_AT_ANCHOR_ONLY','limitation':'SINGLE_MODE; FINITE_DIFFERENCE_INITIAL_VELOCITY_NOISE'})
   with (output/'euler_one_mode_conditional_metrics.csv').open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(cond[0]));w.writeheader();w.writerows(cond)
   status['one_mode_conditional_forecasts']=cond
   status['gates']['E4_CONDITIONAL_ONE_MODE']='DEVELOPMENT_EVALUATED_ONE_MODE_ASSUMPTION'
   status['gates']['E5_BASELINE_COMPARISON']='REVIEW_NOT_GEOMETRY_CERTIFIED'
   status['scientific_status']='DEVELOPMENT_EULER_LINEAR_MODAL_NOT_CERTIFIED'
   # fixed index 0 in validation set chosen before reading responses
   curves=np.arange(1500)*dt,y[0],out_euler[0]
 except Exception as e:
  status['scientific_status']='BLOCKED_FAIL_CLOSED_ERROR';status['blocker']=f'{type(e).__name__}: {e}'
 return write(status,output,curves)

def write(status,output,curves):
 p=Path(output)
 (p/'v050_report.json').write_text(json.dumps(status,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')
 s=['# F005 v0.5.0 - independent linear Euler baseline','',f"**Status:** `{status['scientific_status']}`",'', '## Gates','']
 s += [f'- **{k}**: `{v}`' for k,v in status['gates'].items()]
 s+=['','## Blocker',str(status.get('blocker','None; see provenance and science contract.')),'','## Interpretation','No full nonlinear Euler, viscosity, or source-native PKLSA simulation is certified. Geometry inputs are never inferred from ARX/oscillator frequencies. TEST/OOD water-height traces not accessed.']
 (p/'V050_SUMMARY.md').write_text('\n'.join(s)+'\n',encoding='utf8')
 try:report_pdf(p/'F005_v0.5.0_LINEAR_EULER_DEVELOPMENT.pdf',status,curves)
 except ImportError:
  (p/'PDF_UNAVAILABLE.txt').write_text('matplotlib missing; install numpy and matplotlib\n')
 return status

def main():
 a=argparse.ArgumentParser();a.add_argument('--root',default='.');a.add_argument('--geometry',default='config/EULER_GEOMETRY_REQUIRED.json');a.add_argument('--output',default='outputs/f005_independent_euler_v0.5.0');a.add_argument('--demo',action='store_true')
 z=a.parse_args();root=Path(z.root).resolve();st=run(root,root/z.geometry,root/z.output,demo=z.demo)
 print(json.dumps({'status':st['scientific_status'],'blocker':st.get('blocker'),'output':str(root/z.output)},ensure_ascii=False))
 return 0 if (z.demo or st['scientific_status'].startswith('DEVELOPMENT_EULER')) else 2
if __name__=='__main__':sys.exit(main())
