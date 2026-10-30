"""A074 v0.3.0 P1--P3 only. No gravity target, stability, load or reveal.

P1: pinned Gilbert seed and exact v0.2 discovery candidate reused everywhere.
P2: full-field 3D Euler vorticity relative-equilibrium residual, not marker fit.
P3: fixed-time spatial, finite-core and independent temporal diagnostics.

All coordinates are explicitly MODEL-SCALE SI numbers, not SST physical length.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
import numpy as np
from .euler3d import Euler3D
from .model import load_seed,sample_seed,relative_equilibrium_residual,min_nonlocal_distance,length
from .search_stationary import shape

ROOT=Path(__file__).resolve().parents[1]
PREFIX='A074_Max_Transfer_Force_Trefoil_v0.3.0'
BASE_OUTPUT=ROOT/(PREFIX+'-outputs')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def write(path,x):
 path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
 path.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf8')

def prepared_state():
 selection_path=ROOT/'preregistration/EQUILIBRIUM_SEARCH_v0.2.0.json'
 selected=json.loads(selection_path.read_text(encoding='utf8'))
 seed_path=ROOT/'seeds/trefoil_ideal_3_1_1.json';seed=load_seed(seed_path)
 cfg=json.loads((ROOT/'configs/qualification.json').read_text(encoding='utf8'))
 if selected['schema']!='SST-REL-EQUILIBRIUM-SEARCH-1' or selected['source']!='gilbert 3:1:1':raise ValueError('Unexpected v0.2 discovery source')
 if tuple(selected['parameter_vector'])!=tuple(cfg['pinned_candidate']['parameter_vector']) or selected['chosen_core_m']!=cfg['pinned_candidate']['core_radius_m']:raise ValueError('Candidate changed without a new version')
 if selected['selected_discovery_residual']>1:raise ValueError('Candidate residual invalid')
 points=shape(sample_seed(seed,cfg['material_marker_N']),np.asarray(selected['parameter_vector'],dtype=np.float64))
 if not np.isfinite(points).all():raise ValueError('Candidate not finite')
 gap=min_nonlocal_distance(points,max(4,len(points)//12));core=selected['chosen_core_m']
 if gap<=2*core:raise ValueError('Initial finite cores overlap')
 data={'seed_sha256':digest(seed_path),'selection_sha256':digest(selection_path),'cfg_sha256':digest(ROOT/'configs/qualification.json'),
       'candidate_curve_sha256':hashlib.sha256(np.ascontiguousarray(points,dtype='<f8').tobytes()).hexdigest(),
       'candidate_full_input_sha256':hashlib.sha256(canonical({'seed_hash':digest(seed_path),'selection_hash':digest(selection_path),'config_hash':digest(ROOT/'configs/qualification.json')})).hexdigest(),
       'seed_id':seed['id'],'pinned_selection':selected['parameter_vector'],'core_m':core,'length_m':length(points),
       'nonlocal_gap_m':gap,'gap_over_2core':gap/(2*core),'marker_count':len(points)}
 return cfg,points,data

def _orthogonal_fit(omega_t,omega,grads,xyz,vol):
 """Minimize ||omega_t + U.grad omega + (Omega x r).grad omega - Omega x omega||_L2.

 This is the *Euler vorticity field* stationarity condition in a translating,
 rotating frame. A periodic cube does not globally admit rigid rotation;
 the fit is therefore LOCALIZED / DIAGNOSTIC, not periodic equilibrium proof.
 """
 omega=np.asarray(omega); grads=np.asarray(grads)
 # basis for translation and rotation, 6 vector fields, in fixed order.
 basis=[grads[j] for j in range(3)]
 ex=np.array([1.,0.,0.]);ey=np.array([0.,1.,0.]);ez=np.array([0.,0.,1.])
 for e in (ex,ey,ez):
  # cross(e,r) x3 field. cross(e,omega) vorticity rotation field.
  er=np.empty_like(omega); ew=np.empty_like(omega)
  er[0]=e[1]*xyz[2]-e[2]*xyz[1];er[1]=e[2]*xyz[0]-e[0]*xyz[2];er[2]=e[0]*xyz[1]-e[1]*xyz[0]
  ew[0]=e[1]*omega[2]-e[2]*omega[1];ew[1]=e[2]*omega[0]-e[0]*omega[2];ew[2]=e[0]*omega[1]-e[1]*omega[0]
  b=np.sum(er[:,None]*grads,axis=0)-ew
  basis.append(b)
 # Avoid a huge stacked (6,3,N,N,N) matrix. Assemble six-by-six Gram.
 gram=np.empty((6,6));rhs=np.empty(6)
 for a in range(6):
  rhs[a]=float(np.sum(basis[a]*omega_t))*vol
  for b in range(a+1):
   gram[a,b]=gram[b,a]=float(np.sum(basis[a]*basis[b]))*vol
 # regularize nothing: least squares with recorded conditioning.
 coeff=np.linalg.lstsq(gram,-rhs,rcond=1e-12)[0]
 err2=float(np.sum(omega_t*omega_t))*vol + 2*float(coeff@rhs)+float(coeff@gram@coeff)
 energy=float(np.sum(omega_t*omega_t))*vol
 return {'translation_m_s':coeff[:3].tolist(),'rotation_rad_s':coeff[3:].tolist(),
         'relative_euler_field_residual':math.sqrt(max(0.,err2))/max(math.sqrt(energy),1e-30),
         'rms_omega_t_s2':math.sqrt(energy/(xyz.shape[1]**3)) if False else math.sqrt(energy),
         'gram_condition':float(np.linalg.cond(gram)),'gram_rank':int(np.linalg.matrix_rank(gram,tol=1e-10)),
         'residual_l2_s2_sqrt_m3':math.sqrt(max(0.,err2))}

def full_field_residual(m,uh):
 wh=m.curl_hat(uh);omega=m.ifft(wh)
 wt=m.ifft(m.curl_hat(m.rhs(uh)))
 grads=np.stack([m.ifft(1j*m.k[j][None]*wh) for j in range(3)]) # (3 derivative, 3 components, grid)
 axes=np.meshgrid(m.axis,m.axis,m.axis,indexing='ij')
 xyz=np.stack(axes)
 fitted=_orthogonal_fit(wt,omega,grads,xyz,m.dx**3)
 fitted['field_definition']='min || curl(P[u cross omega]) + U.grad(omega) + (Omega cross r).grad(omega) - Omega cross omega || L2'
 fitted['domain_caveat']='Fitted rigid rotation nonperiodic on periodic cube; not a periodic relative equilibrium'
 return fitted

def one_level(n,cfg,curve,identity,*,steps=False):
 m=Euler3D(n,cfg['box_m'],cfg['rho_kg_m3']);core=identity['core_m']
 uh=m.omega_initial(curve,core,cfg['circulation_m2_s'])
 velocities=m.sample(m.ifft(uh),curve)
 markers=relative_equilibrium_residual(curve,velocities)
 field=full_field_residual(m,uh)
 report={'n':n,'dx_m':m.dx,'core_radius_cells':core/m.dx,'core_diameter_cells':2*core/m.dx,
         'free_gap_cells':(identity['nonlocal_gap_m']-2*core)/m.dx,
         'candidate_curve_sha256':identity['candidate_curve_sha256'],
         'candidate_full_input_sha256':identity['candidate_full_input_sha256'],
         'pinned_parameter_vector':identity['pinned_selection'],'initial_marker_fit':markers,
         'full_field_fit':field,'euler_initial_diagnostics':m.diagnostics(uh),'poisson':m.pressure_report(uh)}
 if steps:
  final_time=float(cfg['final_time_s']);max_cfl=float(cfg['max_cfl'])
  vel=m.diagnostics(uh)['velocity_max_m_s']
  dt_bound=max_cfl*m.dx/max(vel,1e-30)
  steps_count=max(2,int(math.ceil(final_time/min(cfg['max_dt_s'],dt_bound))))
  def advance(s):
   dt=final_time/s;x=curve.copy();v=uh.copy();E0=m.diagnostics(v)['energy_J']
   for _ in range(s):
    x=m.tracer_step(v,x,dt);v=m.timestep(v,dt)
    if not np.isfinite(v).all():raise FloatingPointError('nonfinite Euler state')
   d=m.diagnostics(v)
   return {'num_steps':s,'dt_s':dt,'energy_drift':(d['energy_J']-E0)/E0,
           'energy_J':d['energy_J'],'marker_length_m':length(x),'final_pressure':m.pressure_report(v),
           'vorticity_spectrum_unqualified':True}
  report['fixed_time_evolution']=advance(steps_count)
  if n==cfg['temporal_reference_grid_N']:
   report['temporal_refinement']=advance(2*steps_count)
   report['temporal_refinement']['energy_relative_difference']=abs(report['temporal_refinement']['energy_J']-report['fixed_time_evolution']['energy_J'])/max(report['temporal_refinement']['energy_J'],1e-30)
   report['temporal_refinement']['marker_length_relative_difference']=abs(report['temporal_refinement']['marker_length_m']-report['fixed_time_evolution']['marker_length_m'])/max(report['temporal_refinement']['marker_length_m'],1e-30)
 return report

def run(grids=None,*,out=None,time_evolution=True):
 cfg,curve,ident=prepared_state()
 out=Path(out or BASE_OUTPUT);out.mkdir(parents=True,exist_ok=True)
 grids=grids or cfg['smoke_grid_N']
 results={'schema':'SST-A074-V030-P1P3-QUALIFICATION-1','scientific_status':'DEVELOPMENT_DIAGNOSTIC_NOT_PHYSICAL_STABILITY',
          'framework':'1.1.0 RC2 SOURCE_VALIDATED / WINDOWS_CERTIFICATION_PENDING','source':'Gilbert 3:1:1 ideal trefoil',
          'P1':{'status':'PASS_SAME_IMMUTABLE_CANDIDATE','identity':ident},'P2':{'status':'UNRESOLVED_PENDING_FINE_CORE_AND_FULL_FIELD_EQUILIBRIUM'},
          'P3':{'status':'UNRESOLVED_PENDING_RESOLVED_CORE_GAP_AND_SPATIAL_TEMPORAL_CONVERGENCE'},
          'fixed_time_s':cfg['final_time_s'],'grids':[],'run_grids':grids,
          'disabled_tranches':['P4 stability','P5 force/clamps','P6 scaling or reveal'],'target_constants_used':False}
 write(out/'P1_CANDIDATE_IDENTITY.json',results['P1'])
 for i,n in enumerate(grids):
  print(f'[A074][P2/P3] START grid {n}^3; {i+1}/{len(grids)}',flush=True)
  result=one_level(n,cfg,curve,ident,steps=time_evolution)
  results['grids'].append(result);write(out/f'P2_P3_GRID_{n}.json',result)
  print(f'[A074] grid {n}^3 marker={result["initial_marker_fit"]["normal_residual"]:.6f}, full_field={result["full_field_fit"]["relative_euler_field_residual"]:.6f}; core_cells={result["core_radius_cells"]:.2f}',flush=True)
  write(out/'P1_P3_QUALIFICATION_SUMMARY.json',results)
 fits=[r['full_field_fit']['relative_euler_field_residual'] for r in results['grids']]
 core_good=[r['core_radius_cells']>=cfg['min_core_cells'] and r['free_gap_cells']>=cfg['min_gap_cells'] for r in results['grids']]
 found=any(f<=cfg['relative_field_residual_limit'] for f in fits)
 if not found:results['P2']['status']='NO_EQUILIBRIUM_CANDIDATE_WITHIN_TESTED_GRID_AND_FIXED_GEOMETRY'
 results['P2']['minimum_field_relative_residual']=min(fits)
 results['P2']['candidate_threshold']=cfg['relative_field_residual_limit']
 results['P2']['qualification']='DIAGNOSTIC_ONLY' if not all(core_good) else 'NOT_PHYSICALLY_CERTIFIED'
 results['P3']['core_resolution_status']=core_good
 results['P3']['required_core_radius_cells']=cfg['min_core_cells']
 results['P3']['required_free_gap_cells']=cfg['min_gap_cells']
 if len(results['grids'])>=2:
  a,b=results['grids'][-2:]
  results['P3']['last_pair_relative_field_residual_difference']=abs(b['full_field_fit']['relative_euler_field_residual']-a['full_field_fit']['relative_euler_field_residual'])/max(abs(b['full_field_fit']['relative_euler_field_residual']),1e-30)
  if time_evolution:
   for key in ['energy_J','marker_length_m']:
    results['P3']['last_pair_'+key+'_difference']=abs(b['fixed_time_evolution'][key]-a['fixed_time_evolution'][key])/max(abs(b['fixed_time_evolution'][key]),1e-30)
 results['P3']['status']='UNRESOLVED' # explicit: never infer continuum convergence from 2 grids alone
 results['all_original_inputs_identical']=all(r['candidate_full_input_sha256']==ident['candidate_full_input_sha256'] for r in results['grids'])
 write(out/'P1_P3_QUALIFICATION_SUMMARY.json',results)
 print('P1:',results['P1']['status'],'P2:',results['P2']['status'],'P3:',results['P3']['status'],flush=True)
 return results

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--grids',default='32,48,64');p.add_argument('--out',default=None)
 p.add_argument('--skip-time-evolution',action='store_true');ar=p.parse_args(argv)
 grids=[int(x) for x in ar.grids.split(',')];cfg=json.loads((ROOT/'configs/qualification.json').read_text())
 if not set(grids).issubset(set(cfg['permitted_grid_N'])):p.error('Only declared grids permitted')
 run(grids,out=ar.out,time_evolution=not ar.skip_time_evolution)
if __name__=='__main__':main()
