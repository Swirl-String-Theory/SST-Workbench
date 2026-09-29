from __future__ import annotations
import json,hashlib,platform,sys,os
from pathlib import Path
import numpy as np
from .geometry import curve_metrics,resample_closed
from .filament import evolve_curve
from .field import normalized_velocity_on_grid,pressure_like,divergence_rms,gradient_rms
from .analysis import variance_scaling_scalar,variance_scaling_vector,shuffled_scaling,fit_power,radial_autocorrelation,smooth_periodic,temporal_integrated_variance,fit_temporal
from .temporal import memory_metrics,shuffled_memory_null,memory_convergence
from .persistence import modal_persistence_metrics,numerical_convergence
from .io import write_json,write_csv,sha256
ROOT=Path(__file__).resolve().parents[1]

def clean(x):
 if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list): return [clean(v) for v in x]
 if isinstance(x,(np.bool_,bool)): return bool(x)
 if isinstance(x,(np.integer,int)): return int(x)
 if isinstance(x,(np.floating,float)): return None if not np.isfinite(x) else float(x)
 return x

def env(): return {'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'cpu_count':os.cpu_count()}
def load_manifest(cfg): return json.loads((ROOT/cfg['external_geometry_gate']['staged_manifest']).read_text(encoding='utf-8'))
def load_entry(e):
 p=ROOT/e['file']; h=hashlib.sha256(p.read_bytes()).hexdigest()
 if h!=e['sha256']: raise RuntimeError(f'staged hash mismatch: {e["carrier_id"]}')
 return np.asarray(np.load(p,allow_pickle=False)['points'],float)
def sample_indices(total,every):
 a=list(range(0,int(total)+1,int(every)))
 if a[-1]!=int(total): a.append(int(total))
 return a

def legacy_memory(arr,eff_dt,cfg,rng):
 mem=memory_metrics(arr,eff_dt,max_lag=int(cfg['max_lag_samples'])); null=shuffled_memory_null(arr,eff_dt,int(cfg['shuffle_repeats']),rng,max_lag=int(cfg['max_lag_samples']))
 ratio=float(mem['memory_steps']/max(null['memory_steps_mean'],1e-12)) if np.isfinite(mem['memory_steps']) else float('nan'); excess=float(mem['lag1']-null['lag1_mean']) if np.isfinite(mem['lag1']) else float('nan')
 passed=bool(np.isfinite(ratio) and np.isfinite(excess) and ratio>=float(cfg['memory_ratio_min']) and excess>=float(cfg['lag1_excess_min']))
 return {**mem,'null':null,'memory_ratio_to_null':ratio,'lag1_excess':excess,'pass':passed,'status':'TEMPORAL_MEMORY_RESOLVED' if passed else 'TEMPORAL_MEMORY_NOT_RESOLVED'}

def field_memory(points,cfg,label):
 grid=int(cfg['grid_n']); core=float(cfg['core_ratio']); max_steps=int(cfg['temporal_memory_steps']); frames=evolve_curve(points,core,float(cfg['time_step']),max_steps,int(cfg['reparameterize_every']),int(cfg['field_chunk']))
 spatial=set(sample_indices(int(cfg['spatial_gate_steps']),int(cfg['sample_every']))); mind=sample_indices(max_steps,int(cfg['sample_every']))
 radii=[r for r in map(int,cfg['window_radii_cells']) if r<grid//2]; rng=np.random.default_rng(int(cfg['seed'])+sum(map(ord,label))+grid)
 probes=rng.integers(0,grid,size=(int(cfg['probe_count']),3)); series=[]; steps=[]; vp=[]; vu=[]; vn=[]; div=[]; corr=[]
 for s in mind:
  u,dx=normalized_velocity_on_grid(frames[s],grid,float(cfg['box_half_extent']),core,int(cfg['field_chunk'])); pr,src=pressure_like(u,dx); sm=smooth_periodic(pr,int(cfg['probe_radius_cells'])); series.append(np.asarray([sm[tuple(ix)] for ix in probes],float)); steps.append(int(s))
  if s in spatial:
   d=divergence_rms(u,dx); g=gradient_rms(u,dx); div.append(d/max(g,1e-30)); vp.append(variance_scaling_scalar(pr,radii)); vu.append(variance_scaling_vector(u,radii)); vn.append(shuffled_scaling(pr,radii,int(cfg['null_shuffle_repeats']),rng)); _,cl=radial_autocorrelation(pr); corr.append(cl)
 vp=np.mean(np.asarray(vp),0); vu=np.mean(np.asarray(vu),0); vn=np.mean(np.asarray(vn),0); fp=fit_power(radii,vp,int(cfg['fit_min_radius_cells'])); fu=fit_power(radii,vu,int(cfg['fit_min_radius_cells'])); fn=fit_power(radii,vn,int(cfg['fit_min_radius_cells']))
 arr=np.asarray(series); eff=float(cfg['time_step'])*int(cfg['sample_every']); tt,tv=temporal_integrated_variance(arr,eff); tf=fit_temporal(tt,tv); mg=legacy_memory(arr,eff,cfg['temporal_memory_gate'],rng); mc=memory_convergence(arr,steps,eff,cfg['temporal_memory_convergence_gate'],cfg['temporal_memory_gate'],rng)
 spatial_pass=bool(fp['r2']>=float(cfg['power_fit_r2_min']) and fn['exponent']-fp['exponent']>=float(cfg['null_gap_min']))
 return {'geometry':curve_metrics(points),'pressure_fit':fp,'velocity_fit':fu,'null_fit':fn,'temporal_fit':tf,'mean_divergence_ratio':float(np.mean(div)),'mean_corr_length_cells':float(np.mean(corr)),'spatial_pass':spatial_pass,'memory_gate':mg,'memory_convergence':mc}

def run_modal(points,cfg):
 fr=evolve_curve(points,float(cfg['core_ratio']),float(cfg['time_step']),int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
 return modal_persistence_metrics(fr,float(cfg['time_step']),cfg['modal_persistence_gate'],cfg['kelvin_gate'])

def main_run(config_path,out_dir):
 cfg=json.loads(Path(config_path).read_text(encoding='utf-8')); man=load_manifest(cfg); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); write_json(out/'config_used.json',cfg); write_json(out/'environment.json',env()); write_json(out/'staged_manifest_used.json',man)
 groups={}
 for e in man['entries']: groups.setdefault(e['group_id'],[]).append(e)
 base_rows=[]; carrier_rows=[]; diagnostic=[]
 for gid,ents in sorted(groups.items()):
  base_e=next(e for e in ents if e['role']=='baseline'); base=load_entry(base_e); pm=run_modal(base,cfg); fm=field_memory(base,cfg,gid) if base_e['primary'] else None
  holds=[]
  for e in sorted([x for x in ents if x['role']=='holdout'],key=lambda x:x['carrier_id']):
   hp=run_modal(load_entry(e),cfg); holds.append({'carrier_id':e['carrier_id'],'persistence':hp,'perturbation_rms':e['perturbation_rms']}); carrier_rows.append({'carrier_id':e['carrier_id'],'group_id':gid,'role':'holdout','pass':hp['pass'],'persistent_mode':hp['persistent_mode'],'qualified_late_checkpoints':hp['qualified_late_checkpoints'],'frequency_cv':hp['frequency_cv'],'final_checkpoint_qualified':hp['final_checkpoint_qualified']})
  if not base_e['primary']:
   diagnostic.append({'group_id':gid,'persistence':pm}); carrier_rows.append({'carrier_id':base_e['carrier_id'],'group_id':gid,'role':'diagnostic_baseline','pass':pm['pass'],'persistent_mode':pm['persistent_mode'],'qualified_late_checkpoints':pm['qualified_late_checkpoints'],'frequency_cv':pm['frequency_cv'],'final_checkpoint_qualified':pm['final_checkpoint_qualified']}); print(f'[v0.3.0] {gid} diagnostic done',flush=True); continue
  same=[h for h in holds if pm['pass'] and h['persistence']['pass'] and h['persistence']['persistent_mode']==pm['persistent_mode']]
  robust=bool(pm['pass'] and len(same)>=int(cfg['external_geometry_gate']['minimum_same_branch_holdouts']))
  row={'group_id':gid,'source_group_id':base_e['source_group_id'],'baseline':pm,'holdouts':holds,'same_branch_holdout_count':len(same),'holdout_count':len(holds),'robust':robust,'field_memory':fm}; base_rows.append(row)
  carrier_rows.append({'carrier_id':base_e['carrier_id'],'group_id':gid,'role':'baseline','pass':pm['pass'],'persistent_mode':pm['persistent_mode'],'qualified_late_checkpoints':pm['qualified_late_checkpoints'],'frequency_cv':pm['frequency_cv'],'final_checkpoint_qualified':pm['final_checkpoint_qualified']})
  print(f'[v0.3.0] {gid} primary done robust={robust}',flush=True)
 # Anonymous source group gate.
 sg=[]
 for sid,need in sorted(cfg['external_geometry_gate']['source_group_minimum_robust_bases'].items()):
  rr=[r for r in base_rows if r['source_group_id']==sid]; n=sum(r['robust'] for r in rr); sg.append({'source_group_id':sid,'robust_base_count':int(n),'base_count':len(rr),'minimum_required':int(need),'pass':bool(n>=int(need))})
 modal_transfer=sum(x['pass'] for x in sg)>=int(cfg['external_geometry_gate']['minimum_source_groups_confirmed'])
 present=sum(bool(r['field_memory']['memory_convergence'].get('present_final_two',False)) for r in base_rows); converged=sum(bool(r['field_memory']['memory_convergence'].get('converged',False)) for r in base_rows)
 mem_present=present>=int(cfg['temporal_memory_convergence_gate']['minimum_present_bases']); mem_conv=converged>=int(cfg['temporal_memory_convergence_gate']['minimum_converged_bases'])
 spatial=sum(bool(r['field_memory']['spatial_pass']) for r in base_rows); spatial_ok=spatial>=int(cfg['minimum_spatial_bases']); div_ok=all(r['field_memory']['mean_divergence_ratio']<1e-10 for r in base_rows)
 conv=[]; modal_conv=modal_transfer
 if modal_transfer and cfg['modal_numerical_convergence_gate']['enabled']:
  for x in sg:
   rr=sorted([r for r in base_rows if r['source_group_id']==x['source_group_id'] and r['robust']],key=lambda r:r['group_id'])
   if not rr: continue
   r=rr[0]; be=next(e for e in man['entries'] if e['group_id']==r['group_id'] and e['role']=='baseline'); q=load_entry(be); z=numerical_convergence(q,r['baseline']['persistent_mode'],float(cfg['core_ratio']),int(cfg['reparameterize_every']),int(cfg['field_chunk']),cfg['modal_numerical_convergence_gate'],cfg['kelvin_gate']); z['group_id']=r['group_id']; z['source_group_id']=r['source_group_id']; conv.append(z)
  modal_conv=bool(len(conv)==len(sg) and all(z['pass'] for z in conv))
 if not (spatial_ok and div_ok): verdict='NUMERICAL_QUALIFICATION_FAILED'
 elif not modal_transfer: verdict='REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED'
 elif not modal_conv: verdict='REAL_GEOMETRY_MODAL_TRANSFER_NONCONVERGENT'
 elif not mem_present: verdict='MODAL_TRANSFERRED_MEMORY_NOT_TRANSFERRED'
 elif not mem_conv: verdict='MODAL_TRANSFERRED_MEMORY_NOT_CONVERGED'
 else: verdict='REAL_GEOMETRY_STRUCTURED_MEMORY_AND_MODAL_TRANSFER_CONFIRMED'
 result={'stage':'blind_complete','blind':True,'version':'v0.3.0','verdict':verdict,'modal_transfer_gate':{'pass':modal_transfer,'numerically_converged':modal_conv,'source_groups':sg},'temporal_memory_transfer_gate':{'present':mem_present,'present_base_count':int(present),'converged':mem_conv,'converged_base_count':int(converged),'base_count':len(base_rows)},'spatial_gate':{'pass':spatial_ok,'qualified_base_count':int(spatial),'base_count':len(base_rows)},'divergence_gate':bool(div_ok),'primary_bases':base_rows,'diagnostic_bases':diagnostic,'modal_numerical_convergence':conv,'floquet_policy':cfg['floquet_policy'],'limitations':['Primary dynamics are dimensionless and use externally staged geometry; no absolute theory-specific constants enter the blind verdict.','Source/provider identities are hidden behind anonymous source groups until reveal.','A robust transverse mode is a numerical filament-dynamics result; it is not by itself proof of a physical Kelvin wave.','The primary panel samples a finite subset of qualified external embeddings and does not establish a theorem for all embeddings of the topology.','No recurrence was preregistered, so no Floquet/RPO inference is made.']}
 result=clean(result); write_json(out/'blind_results.json',result)
 # Flat summaries.
 write_csv(out/'modal_persistence_carriers.csv',carrier_rows)
 write_csv(out/'source_group_gate.csv',sg)
 brows=[]; mrows=[]
 for r in base_rows:
  f=r['field_memory']; brows.append({'group_id':r['group_id'],'source_group_id':r['source_group_id'],'robust':r['robust'],'baseline_mode':r['baseline']['persistent_mode'],'same_branch_holdouts':r['same_branch_holdout_count'],'pressure_exponent':f['pressure_fit']['exponent'],'pressure_r2':f['pressure_fit']['r2'],'null_exponent':f['null_fit']['exponent'],'mean_divergence_ratio':f['mean_divergence_ratio']}); mc=f['memory_convergence']; mg=f['memory_gate']; mrows.append({'group_id':r['group_id'],'source_group_id':r['source_group_id'],'memory_pass':mg['pass'],'memory_ratio_to_null':mg['memory_ratio_to_null'],'lag1_excess':mg['lag1_excess'],'present_final_two':mc.get('present_final_two'),'converged':mc.get('converged'),'final_relative_change':mc.get('final_relative_change'),'final_bootstrap_ci_overlap':mc.get('final_bootstrap_ci_overlap')})
 write_csv(out/'real_geometry_base_summary.csv',brows); write_csv(out/'temporal_memory_transfer.csv',mrows); write_csv(out/'modal_numerical_convergence.csv',[{'group_id':z['group_id'],'source_group_id':z['source_group_id'],'status':z['status'],'pass':z['pass'],'base_mode':z['base_mode'],'resolution_frequency_relative_span':z['resolution_frequency_relative_span'],'timestep_frequency_relative_span':z['timestep_frequency_relative_span']} for z in conv])
 dig=sha256(out/'blind_results.json'); (out/'blind_results.sha256').write_text(dig+'  blind_results.json\n',encoding='utf-8')
 return result
