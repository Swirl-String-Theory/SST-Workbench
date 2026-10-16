from __future__ import annotations
from pathlib import Path
import json,math
import numpy as np
from .metrics import read_xyz,curve_metrics,shape_distance

def _rel(a,b):
    vals={}
    for k in ('L_over_Rg','edge_cv'):
        aa=float(a[k]);bb=float(b[k]);vals[k]=abs(bb-aa)/max(abs(aa),abs(bb),1e-12)
    return max(vals.values()),vals

def analyze(root:Path):
    cfg=json.loads((root/'configs/default.json').read_text(encoding='utf-8'));mp=root/'campaign/manifest_pilot.json';rp=root/'campaign/runlog_pilot.json';rt=root/'campaign/runtime_pilot.json'
    if not mp.exists():return {'available':False,'reason':'manifest_pilot.json missing'}
    man=json.loads(mp.read_text(encoding='utf-8')); conds=man['conditions'];runpayload=json.loads(rp.read_text(encoding='utf-8')) if rp.exists() else {'conditions':[]};runlog=runpayload.get('conditions',[]);runtime=json.loads(rt.read_text(encoding='utf-8')) if rt.exists() else {};byrun={r['condition_id']:r for r in runlog}
    finals={};errors=[]
    for c in conds:
        p=root/'campaign/results'/c['condition_id']/'final.txt'
        try: finals[c['condition_id']]=read_xyz(p)
        except Exception as e:errors.append({'condition_id':c['condition_id'],'error':str(e)})
    complete=(len(conds)-len(errors))/len(conds) if conds else 0.0
    refs={c['reference_id']:c for c in conds if c['role']=='reference'};responses=[]
    def scal(x):
        m=curve_metrics(x);rg=float(m['rg']);return {'L_over_Rg':float(m['length'])/rg,'edge_cv':float(m['edge_cv'])}
    for c in conds:
        if c['role']!='sweep' or c['condition_id'] not in finals or refs[c['reference_id']]['condition_id'] not in finals:continue
        cid=c['condition_id'];rid=refs[c['reference_id']]['condition_id'];sd=float(shape_distance(finals[rid],finals[cid],m=128));sr,parts=_rel(scal(finals[rid]),scal(finals[cid]));rr=byrun.get(cid,{});rref=byrun.get(rid,{});it=int(rr.get('iterations',0));it0=max(int(rref.get('iterations',0)),1);responses.append({'axis_id':c['axis_id'],'condition_id':cid,'reference_condition_id':rid,'multiplier':c['multiplier'],'x_log2':c['x_log2'],'k':c['k'],'level_kind':c['level_kind'],'shape_distance':sd,'scalar_rel_max':sr,'scalar_components':parts,'iterations':it,'reference_iterations':it0,'iteration_ratio':it/it0 if it0 else math.nan,'converged':bool(rr.get('converged',False))})
    activation=[]
    for c in conds:
        if c['role']!='activation_control':continue
        match=refs.get(c['reference_id'])
        if not match: continue
        cid=c['condition_id'];rid=match['condition_id']
        row={'control_id':cid,'active_reference_id':rid,'sector_id':c['sector_id'],
             'switch_state':'off','active_switch_state':'on',
             'numeric_defaults_held':True,
             'condition_pass':byrun.get(cid,{}).get('status')=='PASS',
             'reference_pass':byrun.get(rid,{}).get('status')=='PASS',
             'both_converged':bool(byrun.get(cid,{}).get('converged')) and bool(byrun.get(rid,{}).get('converged')),
             'off_switch_readback_verified':bool(byrun.get(cid,{}).get('parameter_state_start',{}).get('switch_reported')) and bool(byrun.get(cid,{}).get('parameter_state_final',{}).get('switch_reported'))}
        if cid in finals and rid in finals:
            row['shape_distance']=float(shape_distance(finals[rid],finals[cid],m=128))
            row['scalar_rel_max'],row['scalar_components']=_rel(scal(finals[rid]),scal(finals[cid]))
            i0=max(int(byrun.get(rid,{}).get('iterations',0)),1)
            row['iteration_ratio']=int(byrun.get(cid,{}).get('iterations',0))/i0
        else:row['error']='missing one or both final coordinates'
        activation.append(row)
    ladder_ok=True
    for r in responses:
        if r['k'] is not None:ladder_ok &= abs(float(r['multiplier'])-2.0**(float(r['k'])/4.0))<=1e-14
    axes={a:[] for a in cfg['axes']}
    for r in responses:axes[r['axis_id']].append(r)
    summaries={};fits={}
    for a,rr in axes.items():
        local=[r for r in rr if r['x_log2'] is not None and abs(float(r['x_log2']))==0.25];ext=[r for r in rr if r['k'] in (-16,16)];zero=next((r for r in rr if r['level_kind']=='zero'),None);fitpts=[r for r in rr if r['x_log2'] is not None and abs(float(r['x_log2']))<=cfg['thresholds']['quadratic_local_abs_log2']]
        shape_effect=max([r['shape_distance'] for r in rr],default=math.nan);scalar_effect=max([r['scalar_rel_max'] for r in rr],default=math.nan);iter_effect=max([abs(float(r['iteration_ratio'])-1.0) for r in rr if math.isfinite(float(r['iteration_ratio']))],default=math.nan)
        summaries[a]={'n':len(rr),'converged_fraction':sum(bool(r['converged']) for r in rr)/len(rr) if rr else 0.0,'local_max_shape':max([r['shape_distance'] for r in local],default=math.nan),'extreme_max_shape':max([r['shape_distance'] for r in ext],default=math.nan),'max_shape':shape_effect,'max_scalar_rel':scalar_effect,'max_iteration_fraction_change':iter_effect,'zero_endpoint':zero}
        if len(fitpts)>=5:
            xx=np.array([r['x_log2'] for r in fitpts],float);yy=np.array([r['shape_distance'] for r in fitpts],float);co=np.polyfit(xx,yy,2);pred=np.polyval(co,xx);ssr=float(np.sum((yy-pred)**2));sst=float(np.sum((yy-yy.mean())**2));fits[a]={'a':float(co[0]),'b':float(co[1]),'c':float(co[2]),'r2':1-ssr/sst if sst>0 else 1.0,'n':len(fitpts)}
        else:fits[a]={'r2':math.nan,'n':len(fitpts)}
    # Anonymous special diagnostics. S5: tangential redistribution, S6: drag/damping,
    # S7: velocity-dependent force deliberately exercised under the requested Damped regime.
    special={
      'S5':{'interpretation':'parameterization_vs_shape','max_edge_cv_rel':max([r['scalar_components']['edge_cv'] for r in axes.get('S5',[])],default=math.nan),'max_shape':max([r['shape_distance'] for r in axes.get('S5',[])],default=math.nan)},
      'S6':{'interpretation':'relaxation_time_vs_final_shape','max_iteration_fraction_change':max([abs(r['iteration_ratio']-1.0) for r in axes.get('S6',[]) if math.isfinite(r['iteration_ratio'])],default=math.nan),'max_shape':max([r['shape_distance'] for r in axes.get('S6',[])],default=math.nan)},
      'S7':{'interpretation':'velocity_dependent_force_in_damped_regime','max_iteration_fraction_change':max([abs(r['iteration_ratio']-1.0) for r in axes.get('S7',[]) if math.isfinite(r['iteration_ratio'])],default=math.nan),'max_shape':max([r['shape_distance'] for r in axes.get('S7',[])],default=math.nan),'regime_caveat':'KnotPlot GUI note says Undamped is intended when velocity-dependent force is enabled; this campaign intentionally retains Damped per protocol.'}
    }
    return {'schema':'A058-SLIDER-ANALYSIS-7','available':True,'condition_count':len(conds),'expected_condition_count':271,'reference_count':len(refs),'axis_count':8,'coordinate_complete_fraction':complete,'parse_errors':errors,'runlog_entries':len(runlog),'run_failures':sum(r.get('status')!='PASS' for r in runlog),'run_nonconverged':sum(not r.get('converged',False) for r in runlog),'parameter_state_verified_fraction':sum(bool(r.get('parameter_state_verified')) for r in runlog)/len(runlog) if runlog else 0.0,'safe_final_verified_fraction':sum(bool(r.get('safe_final_verified')) for r in runlog)/len(runlog) if runlog else 0.0,'ladder_ok':bool(ladder_ok),'runtime':runtime,'shared_seed_sha256':man.get('shared_seed_sha256'),'shared_seed_provenance_verified':bool(man.get('shared_seed_sha256') and runtime.get('shared_seed_sha256')==man.get('shared_seed_sha256') and len(runlog)==len(conds) and all(r.get('shared_seed_sha256')==man.get('shared_seed_sha256') for r in runlog)),'responses':responses,'axis_summaries':summaries,'quadratic_local_fits':fits,'special_diagnostics':special,'activation_controls':activation,'activation_control_count':len(activation)}
