#!/usr/bin/env python3
"""Read deterministic chunk outputs; derive body-frame phase, shape return, period consistency."""
from __future__ import annotations
import json,csv,math,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rolling_clock import ROOT,A006
R=ROOT/'results'
RUNS={'n192':1,'main':5,'n288_halfdt':1,'n384':2,'n512':4,'n512_halfdt':2}

def load(prefix,num):
 rows=[];coords=[]
 for k in range(num):
  z=np.load(R/f'{prefix}_chunk{k}.npz')
  r=json.loads(str(z['metrics_json']))
  if k:
   rows+=r[1:];coords.extend(z['Xs'][1:])
  else:
   rows+=r;coords.extend(z['Xs'])
 t=np.array([row['tau'] for row in rows]);p=np.unwrap([row['raw_phase'] for row in rows]);p-=p[0]
 Om=np.array([row['body_omega_z'] for row in rows]); alpha=np.r_[0,np.cumsum(np.diff(t)*(Om[1:]+Om[:-1])*.5)]
 internal=p+3*alpha
 for j,row in enumerate(rows):
  row['raw_phase_unwrapped']=float(p[j]);row['rigid_rotation_integral_rad']=float(alpha[j]);row['internal_mode_phase_rad']=float(internal[j]);row['relative_roll_phase_rad']=float(internal[j]/2)
  row['body_frame_geometric_coherence']=row['coherence']
 return rows, np.array(coords)

def curve_dense(X,multiple=8):
 s=np.arange(multiple,dtype=float)/multiple
 return ((1-s)[:,None,None]*X[None,:,:]+s[:,None,None]*np.roll(X,-1,axis=0)[None,:,:]).reshape(-1,3)

def chamfer(X,RefTree,refdense,alpha):
 c=X-X.mean(axis=0);co=np.cos(alpha);si=np.sin(alpha)
 rot=np.array([[co,si,0],[-si,co,0],[0,0,1]],float)
 points=curve_dense(c@rot.T)
 dist1=RefTree.query(points,k=1,workers=-1)[0]
 dist2=cKDTree(points).query(refdense,k=1,workers=-1)[0]
 return float(np.sqrt(.5*(np.mean(dist1**2)+np.mean(dist2**2))))

def crossings(t,p):
 sign=-1 if p[-1]<0 else 1;pp=sign*p
 targets=2*np.pi*np.arange(1,int(np.floor(pp[-1]/(2*np.pi)))+1)
 times=np.interp(targets,pp,t)
 return times,np.diff(np.r_[0,times])

def report_run(name,num):
 rows,coords=load(name,num)
 t=np.array([r['tau'] for r in rows]);raw=np.array([r['raw_phase_unwrapped'] for r in rows]);rel=np.array([r['relative_roll_phase_rad'] for r in rows]);alpha=np.array([r['rigid_rotation_integral_rad'] for r in rows]);amp=np.array([r['coherence'] for r in rows]);
 raw_times,periods=crossings(t,raw)
 initial=coords[0]-coords[0].mean(axis=0);refd=curve_dense(initial);tree=cKDTree(refd)
 idxs=np.unique(np.r_[np.arange(0,len(t),max(1,len(t)//40)),len(t)-1,np.searchsorted(t,raw_times)])
 shape_rms=[]
 for j in idxs: shape_rms.append((float(t[j]),chamfer(coords[j],tree,refd,alpha[j])))
 summary={'run':name,'N':len(coords[0]),'time_step':t[1]-t[0] if len(t)>1 else 0,
  'final_tau':float(t[-1]),'raw_pattern_cycles':float(raw[-1]/(2*np.pi)),
  'body_revolutions':float(alpha[-1]/(2*np.pi)),
  'body_subtracted_poloidal_revolutions':float(rel[-1]/(2*np.pi)),
  'raw_full_periods_count':int(len(periods)),
  'raw_period_median':float(np.median(periods)) if len(periods) else None,
  'raw_period_rel_cv':float(np.std(periods)/np.mean(periods)) if len(periods)>1 else None,
  'raw_period_first':float(periods[0]) if len(periods) else None,
  'raw_period_last':float(periods[-1]) if len(periods) else None,
  'amplitude_min':float(amp.min()),'amplitude_end':float(amp[-1]),
  'relative_roll_peak_abs_revolutions':float(np.max(np.abs(rel))/(2*np.pi)),
  'body_omega_initial':rows[0]['body_omega_z'],'body_omega_last':rows[-1]['body_omega_z'],
  'rigid_rotation_least_squares_max_condition':max(r['fit_condition'] for r in rows),
  'radius_max_fractional_change':float(np.max(np.abs(np.array([r['rms_radius'] for r in rows])/rows[0]['rms_radius']-1))),
  'length_max_fractional_change':float(np.max(np.abs(np.array([r['curve_length'] for r in rows])/rows[0]['curve_length']-1))),
  'body_frame_chamfer_at_final_R':float(shape_rms[-1][1]),
  'body_frame_chamfer_max_R':float(max(x[1] for x in shape_rms)),
  'mean_source_pair_distance_initial_R':rows[0]['pair_distance_median'],
  'topology_certified':False}
 with open(R/f'{name}_processed.csv','w',newline='',encoding='utf8') as fp:
  w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with open(R/f'{name}_shape.csv','w',newline='',encoding='utf8') as fp:
  w=csv.writer(fp);w.writerow(['tau','symmetric_rms_chamfer_R']);w.writerows(shape_rms)
 (R/f'{name}_summary.json').write_text(json.dumps(summary,indent=2))
 return rows,summary

def main():
 reports={};series={}
 for name,n in RUNS.items():
  series[name],reports[name]=report_run(name,n)
  print(name,json.dumps({k:reports[name][k] for k in ('N','final_tau','raw_pattern_cycles','body_revolutions','body_subtracted_poloidal_revolutions','raw_full_periods_count','raw_period_median','raw_period_rel_cv','amplitude_min','body_frame_chamfer_max_R')}),flush=True)
 # summary and plots
 tmax=.0525
 fig,ax=plt.subplots(figsize=(9,5))
 for name in ('n192','main','n384','n512','n288_halfdt','n512_halfdt'):
  rr=series[name];tt=np.array([r['tau'] for r in rr]);idx=tt<=tmax+1e-9
  v=np.array([r['relative_roll_phase_rad'] for r in rr])/(2*np.pi)
  ax.plot(tt[idx],v[idx],label=name+f' (N={reports[name]["N"]})')
 ax.axhline(0,linewidth=.8,color='gray');ax.set_xlabel(r'Normalized time $\hat t=\Gamma t/R^2$');ax.set_ylabel('Body-subtracted poloidal turns');ax.set_title('Resolution test: apparent internal rolling collapses at high N')
 ax.legend();fig.tight_layout();fig.savefig(R/'internal_phase_resolution.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,5))
 rr=series['n512'];tt=np.array([r['tau'] for r in rr]); raw=np.array([r['raw_phase_unwrapped'] for r in rr])/(2*np.pi); body=-3*np.array([r['rigid_rotation_integral_rad'] for r in rr])/(2*np.pi)
 residual=np.array([r['internal_mode_phase_rad'] for r in rr])/(2*np.pi)
 ax.plot(tt,raw,label='Observed pattern phase / 2pi');ax.plot(tt,body,label='Expected from rigid-body rotation');ax.plot(tt,residual,label='Difference (mode phase)')
 ax.set_xlabel(r'Normalized time $\hat t$');ax.set_ylabel('Phase winding turns');ax.set_title('N=512: raw winding tracks the rigid rotation');ax.legend();fig.tight_layout();fig.savefig(R/'raw_vs_rigid_phase.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(9,4.5))
 rr=series['n512'];tt=np.array([r['tau'] for r in rr]);amp=np.array([r['coherence'] for r in rr]); ax.plot(tt,amp)
 ax.set_ylim(0.98,1.005);ax.set_xlabel(r'Normalized time $\hat t$');ax.set_ylabel('Winding mode coherence |A|');ax.set_title('Geometric winding coherence; not a material clock')
 fig.tight_layout();fig.savefig(R/'coherence_n512.png',dpi=160);plt.close(fig)
 # scientific assessment based on source data, distinguishes apparent from internal cycles
 out={'status':'DEVELOPMENT: REPEATED GEOMETRIC PATTERN, NO INDEPENDENT INTERNAL CLOCK CERTIFIED',
      'source_sha256':hashlib.sha256(A006.read_bytes()).hexdigest(),
      'scaling':'dimensionless R_ref=Gamma=1; a_sim/R_ref=0.002, vortexlab constant C0=0.1395 delta=0.25',
      'physics':'single closed polygonal filament, VortexLab local LIA+bare nonlocal midpoint; zero external forcing, no center lock',
      'gates':{'G0_reversed_circulation_and_translation_invariance':'PASS unit tests',
               'G1_spatial_convergence_of_body_subtracted_roll':'NOT CONVERGED TO A NONZERO OSCILLATOR; signal shrinks with N',
               'G2_timestep_halfing_at_N288':'PASS on short interval for selected observable',
               'G3_10_raw_pattern_periods':'PASS at N512',
               'G4_10_independent_internal_roll_periods':'NOT DEMONSTRATED',
               'G5_finite_core_Euler_and_isotopy_certificate':'NOT EXECUTED',
               'G6_robustness_under_external_potential_flow':'NOT EXECUTED'},
      'runs':reports}
 (R/'overall_summary.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':main()
