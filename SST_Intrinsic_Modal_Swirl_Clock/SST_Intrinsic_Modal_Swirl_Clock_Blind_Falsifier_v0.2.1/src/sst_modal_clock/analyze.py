from pathlib import Path
import csv,json
import numpy as np
from .blind import load_catalog
from .modal import natural_response,odd_response,even_probe_contamination,learn_modes,project,mode_strain_weights,recurrence_metrics,delayed_stretch_test,trajectory_displacement
from .util import clean_json


def _load(p): return np.load(p,allow_pickle=False)
def _truth(x): return str(x).lower() in ('true','1','yes')
def _savecsv(path,rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['carrier_id']
    with open(path,'w',newline='',encoding='utf-8') as f:
        z=csv.DictWriter(f,fieldnames=fields);z.writeheader();z.writerows([{k:(json.dumps(clean_json(v),sort_keys=True) if isinstance(v,(list,dict,tuple)) else v) for k,v in r.items()} for r in rows])

def _pairs(work):
    pairs={}
    for r in load_catalog(work): pairs.setdefault(r['pair_id'],[]).append(r)
    return pairs

def _arm(rr,arm): return next((r for r in rr if int(r['probe_arm'])==int(arm)),None)
def _stage_a_file(work,r,branch='stage_a'): return Path(work)/f'results_{branch}/candidates'/f'{r["candidate_id"]}.npz'
def _stage_b_file(work,branch,r): return Path(work)/f'results_{branch}/candidates'/f'{r["candidate_id"]}.npz'
def _actual_t(z): return float(np.asarray(z['t'])[-1])

def _stage_a_geometry_metrics(zs,cfg):
    target=float(cfg['stage_a_t_final']); tol=float(cfg.get('gate_stage_a_completion_fraction',.995)); hard=float(cfg.get('gate_max_stage_a_ds_cv',.20)); mesh_gate=float(cfg.get('gate_max_mesh_to_physical_rms_ratio',np.inf))
    complete=bool(all(_actual_t(z)>=tol*target for z in zs))
    maxds=float(max(np.max(z['ds_cv']) for z in zs))
    ratios=[]
    for z in zs:
        ratios.extend((np.asarray(z['mesh_speed_rms'],float)/np.maximum(np.asarray(z['physical_speed_rms'],float),1e-15)).tolist())
    maxratio=float(max(ratios)) if ratios else 0.0
    ok=bool(complete and maxds<=hard and maxratio<=mesh_gate)
    return {'geometry_ok':ok,'completion_ok':complete,'max_ds_cv_stage_a':maxds,'max_mesh_to_physical_rms_ratio':maxratio,'mesh_ratio_ok':bool(maxratio<=mesh_gate),'actual_t_min':float(min(_actual_t(z) for z in zs))}

def _recurrence_gates(rec,ev,cfg,channel,even_ratio):
    sc1=bool(ev>=float(cfg.get('gate_min_discovery_energy',.03)) and rec.get('amplitude',0)>=float(cfg.get('gate_min_holdout_amplitude',1e-5)))
    sc2=bool(rec.get('valid') and rec.get('cycles',0)>=float(cfg.get('gate_min_cycles',4)) and rec.get('spectral_power_fraction',0)>=float(cfg.get('gate_min_spectral_power',.30)) and rec.get('harmonic_r2',0)>=float(cfg.get('gate_min_harmonic_r2',.50)))
    sc3=bool(rec.get('n_return_closures',0)>=int(cfg.get('gate_min_return_closures',3)) and rec.get('multi_return_closure_median',99)<=float(cfg.get('gate_max_multi_return_closure_median',.45)) and rec.get('multi_return_closure_max',99)<=float(cfg.get('gate_max_multi_return_closure_max',.80)))
    sc4=bool(rec.get('period_cv',99)<=float(cfg.get('gate_max_period_cv',.15)) and rec.get('amplitude_cv',99)<=float(cfg.get('gate_max_amplitude_cv',.25)) and rec.get('cycle_mean_drift_fraction',99)<=float(cfg.get('gate_max_cycle_mean_drift_fraction',.35)))
    probe_ok=bool(channel!='odd' or even_ratio<=float(cfg.get('gate_max_even_probe_ratio',.75)))
    return sc1,sc2,sc3,sc4,probe_ok

def _coverage_gate(total,valid,priority_total,priority_valid,cfg):
    frac=float(valid/max(total,1)); minfrac=float(cfg.get('gate_min_valid_carrier_fraction_for_global_fail',.80)); mincount=int(cfg.get('gate_min_valid_carriers_for_global_fail',20))
    priority_ok=bool((not cfg.get('gate_require_all_priority_carriers',True)) or priority_total==priority_valid)
    return {'valid_carrier_fraction':frac,'coverage_ok_for_global_fail':bool(valid>=mincount and frac>=minfrac and priority_ok),'priority_coverage_ok':priority_ok,'gate_min_valid_carrier_fraction_for_global_fail':minfrac,'gate_min_valid_carriers_for_global_fail':mincount}

def analyze_stage_a(work,cfg):
    work=Path(work); out=work/'analysis'; modes_dir=out/'stage_a_modes'; modes_dir.mkdir(parents=True,exist_ok=True)
    rows=[]; carriers=[]; candidate_manifest=[]; disc_t=float(cfg.get('discovery_time',1.2)); eps=float(cfg['probe_eps']); topk=int(cfg.get('top_modes',7)); max_returns=int(cfg.get('max_return_orders',4)); pairs=_pairs(work)
    for pid,rr in sorted(pairs.items()):
        rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); priority=bool(any(bool(r.get('certification_priority',False)) for r in rr)); base={'carrier_id':(rp or rm or r0 or {}).get('carrier_id',''),'pair_id':pid,'certification_priority':priority}
        if not rp or not rm or not r0:
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_ARM'}); continue
        fps=[_stage_a_file(work,r) for r in (rp,rm,r0)]
        if not all(p.exists() for p in fps):
            carriers.append({**base,'geometry_ok':False,'status':'MISSING_TRAJECTORY'}); continue
        zp,zm,z0=map(_load,fps); gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
        n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float)
        carrier_rows=[]; even_ratio=np.inf
        # We may still report partial modal diagnostics, but never certify an incomplete carrier.
        if n>=32:
            nd=int(np.searchsorted(t,disc_t,side='right')); nd=max(12,min(len(t)-16,nd))
            if nd<len(t)-16:
                # truncate all channels to common time; Stage-A candidate still requires gm.geometry_ok.
                class ZView(dict): pass
                def cut(z):
                    return {'x':np.asarray(z['x'][:n]),'x_reference':np.asarray(z['x_reference'])}
                nat,ref=natural_response(cut(z0)); odd,_=odd_response(cut(zp),cut(zm),eps); even=even_probe_contamination(cut(zp),cut(zm),cut(z0))
                even_rms=float(np.sqrt(np.mean(even[:nd]**2))); odd_phys_rms=float(eps*np.sqrt(np.mean(odd[:nd]**2))); even_ratio=even_rms/max(odd_phys_rms,1e-15)
                for channel,response in [('natural',nat),('odd',odd)]:
                    modes,ev,center=learn_modes(response,nd,topk); amps=project(response,modes,center)
                    modefile=modes_dir/f'{rp["carrier_id"]}_{channel}.npz'
                    np.savez_compressed(modefile,modes=modes,energy=ev,center=center,reference=ref,discovery_time=float(t[nd-1]),channel=channel,parameterization_policy='uniform_arclength+cyclic_phase+rigid+normal')
                    for k in range(len(modes)):
                        rec=recurrence_metrics(t[nd:],amps[nd:,k],max_returns=max_returns); sc1,sc2,sc3,sc4,probe_ok=_recurrence_gates(rec,float(ev[k]),cfg,channel,even_ratio)
                        candidate=bool(gm['geometry_ok'] and sc1 and sc2 and sc3 and sc4 and probe_ok)
                        row={**base,'channel':channel,'mode_index':k,'mode_file':str(modefile.relative_to(work)),'discovery_energy_fraction':float(ev[k]),**gm,'even_probe_ratio':even_ratio,'probe_linearity_ok':probe_ok,'SA1_intrinsic_mode':sc1,'SA2_multi_cycle':sc2,'SA3_multi_return_closure':sc3,'SA4_period_amplitude_stationarity':sc4,'stage_a_provisional_candidate':candidate,'stage_a_candidate':False,**{f'material_{a}':b for a,b in rec.items()}}
                        rows.append(row); carrier_rows.append(row)
                        if candidate:
                            candidate_manifest.append({'pair_id':pid,'carrier_id':rp['carrier_id'],'channel':channel,'mode_index':k,'mode_file':str(modefile.relative_to(work)),'period':rec.get('period'),'frequency':rec.get('frequency'),'amplitude':rec.get('amplitude'),'discovery_energy_fraction':float(ev[k]),'closure_median':rec.get('multi_return_closure_median'),'period_cv':rec.get('period_cv'),'amplitude_cv':rec.get('amplitude_cv'),'certification_priority':priority})
        status='VALID' if gm['geometry_ok'] else ('INCOMPLETE_OR_MESH_GATE' if not gm['completion_ok'] else ('MESH_RATIO_GATE' if not gm['mesh_ratio_ok'] else 'DS_CV_GATE'))
        carriers.append({**base,**gm,'status':status,'even_probe_ratio':even_ratio,'n_stage_a_provisional_candidates':sum(int(r['stage_a_provisional_candidate']) for r in carrier_rows)})
    _savecsv(out/'blind_stage_a_modal_results.csv',rows); _savecsv(out/'blind_stage_a_carrier_summary.csv',carriers)
    manifest={'format':'SST-INTRINSIC-MODAL-STAGE-A-PROVISIONAL-CANDIDATES-2.1','candidates':candidate_manifest}; (out/'stage_a_candidates_provisional.json').write_text(json.dumps(clean_json(manifest),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    # compatibility: before gauge certification the final manifest is deliberately empty.
    (out/'stage_a_candidates.json').write_text(json.dumps({'format':'SST-INTRINSIC-MODAL-STAGE-A-CERTIFIED-CANDIDATES-2.1','candidates':[]},indent=2,sort_keys=True)+'\n',encoding='utf-8')
    total=len(carriers); valid=sum(int(r.get('geometry_ok',False)) for r in carriers); ptotal=sum(int(r.get('certification_priority',False)) for r in carriers); pvalid=sum(int(r.get('certification_priority',False) and r.get('geometry_ok',False)) for r in carriers); cov=_coverage_gate(total,valid,ptotal,pvalid,cfg); cand_carriers=len(set(r['carrier_id'] for r in candidate_manifest))
    if candidate_manifest: gate='PASS_PROVISIONAL_STAGE_A_RECURRENCE__MESH_GAUGE_CERTIFICATION_REQUIRED'
    elif cov['coverage_ok_for_global_fail']: gate='FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK'
    else: gate='INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE'
    summary={'format':'SST-INTRINSIC-MODAL-STAGE-A-BLIND-2.1','n_carriers':total,'n_geometry_valid_carriers':valid,'n_priority_carriers':ptotal,'n_priority_geometry_valid_carriers':pvalid,'n_modes_tested':len(rows),'n_stage_a_provisional_candidates':len(candidate_manifest),'carriers_with_stage_a_provisional_candidates':cand_carriers,'carrier_identity_read':False,'qhp_coordinate_used':False,'discovery_time_absolute':disc_t,'modal_channels':['natural','odd'],'parameterization_policy':'uniform arclength resample + cyclic phase alignment + rigid alignment + normal projection','mesh_policy':'segment-length-feedback tangential redistribution; no material-label interpretation','stage_a_core_mode':str(cfg.get('stage_a_core_mode','global_volume')),**cov,'primary_gate':gate}
    (out/'blind_stage_a_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary

def _load_provisional(work):
    p=Path(work)/'analysis/stage_a_candidates_provisional.json'
    return json.loads(p.read_text(encoding='utf-8')).get('candidates',[]) if p.exists() else []

def _load_stage_a_candidates(work):
    p=Path(work)/'analysis/stage_a_candidates.json'
    return json.loads(p.read_text(encoding='utf-8')).get('candidates',[]) if p.exists() else []

def _response_for_channel(channel,zp,zm,z0,eps,ref):
    if channel=='natural': return trajectory_displacement(z0,ref)[0],np.asarray(z0['sigma'],float)
    resp,_=odd_response(zp,zm,eps); sig=.5*(np.asarray(zp['sigma'])-np.asarray(zm['sigma']))/max(eps,1e-15); return resp,sig

def _gauge_response(channel,zp,zm,z0,eps,ref):
    if channel=='natural': return trajectory_displacement(z0,ref)[0]
    return odd_response(zp,zm,eps)[0]

def _rel_spread(vals):
    a=np.asarray([v for v in vals if np.isfinite(v)],float)
    return float((a.max()-a.min())/max(abs(np.median(a)),1e-15)) if len(a)>=2 else np.inf

def analyze_stage_a_gauge(work,cfg):
    work=Path(work); out=work/'analysis'; provisional=_load_provisional(work); pairs=_pairs(work); rows=[]; certified=[]; disc_t=float(cfg.get('discovery_time',1.2)); eps=float(cfg['probe_eps']); max_returns=int(cfg.get('max_return_orders',4))
    for c in provisional:
        rr=pairs.get(c['pair_id'],[]); rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0)
        if not rp or not rm or not r0: continue
        mf=np.load(work/c['mode_file'],allow_pickle=False); mode=np.asarray(mf['modes'][int(c['mode_index'])],float); center=np.asarray(mf['center'],float); ref=np.asarray(mf['reference'],float)
        branch_metrics={}; ok=True
        for branch in ('stage_a_gauge_low','stage_a_gauge_high'):
            fps=[_stage_a_file(work,r,branch) for r in (rp,rm,r0)]
            if not all(p.exists() for p in fps): ok=False; branch_metrics[branch]={'geometry_ok':False,'reason':'MISSING'}; continue
            zp,zm,z0=map(_load,fps); gm=_stage_a_geometry_metrics((zp,zm,z0),cfg); n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float)
            if n<32: ok=False; branch_metrics[branch]={**gm,'reason':'TOO_SHORT'}; continue
            resp=_gauge_response(c['channel'], {'x':zp['x'][:n],'x_reference':zp['x_reference']},{'x':zm['x'][:n],'x_reference':zm['x_reference']},{'x':z0['x'][:n],'x_reference':z0['x_reference']},eps,ref)
            a=project(resp,np.asarray([mode]),center)[:,0]; nd=int(np.searchsorted(t,disc_t,side='right')); nd=max(12,min(n-16,nd)); rec=recurrence_metrics(t[nd:],a[nd:],max_returns=max_returns) if nd<n-16 else {'valid':False}
            _,sc2,sc3,sc4,_=_recurrence_gates(rec,float(c.get('discovery_energy_fraction',1.0) or 1.0),cfg,c['channel'],0.0)
            pass_rec=bool(gm['geometry_ok'] and sc2 and sc3 and sc4); ok &= pass_rec
            branch_metrics[branch]={**gm,'recurrence_ok':pass_rec,**rec}
        nominal=[c.get('period',np.nan),c.get('closure_median',np.nan),c.get('amplitude',np.nan)]
        lo=branch_metrics.get('stage_a_gauge_low',{}); hi=branch_metrics.get('stage_a_gauge_high',{})
        pspread=_rel_spread([nominal[0],lo.get('period',np.nan),hi.get('period',np.nan)])
        cspread=_rel_spread([nominal[1],lo.get('multi_return_closure_median',np.nan),hi.get('multi_return_closure_median',np.nan)])
        aspread=_rel_spread([nominal[2],lo.get('amplitude',np.nan),hi.get('amplitude',np.nan)])
        invariant=bool(ok and pspread<=float(cfg.get('gate_max_mesh_gauge_period_spread',.15)) and cspread<=float(cfg.get('gate_max_mesh_gauge_closure_spread',.35)) and aspread<=float(cfg.get('gate_max_mesh_gauge_amplitude_spread',.35)))
        row={**c,'gauge_low_geometry_ok':lo.get('geometry_ok',False),'gauge_high_geometry_ok':hi.get('geometry_ok',False),'mesh_gauge_period_spread':pspread,'mesh_gauge_closure_spread':cspread,'mesh_gauge_amplitude_spread':aspread,'mesh_gauge_invariant':invariant,'stage_a_candidate':invariant}
        rows.append(row)
        if invariant: certified.append({**c,'mesh_gauge_period_spread':pspread,'mesh_gauge_closure_spread':cspread,'mesh_gauge_amplitude_spread':aspread})
    _savecsv(out/'blind_stage_a_gauge_results.csv',rows)
    manifest={'format':'SST-INTRINSIC-MODAL-STAGE-A-CERTIFIED-CANDIDATES-2.1','candidates':certified}; (out/'stage_a_candidates.json').write_text(json.dumps(clean_json(manifest),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    base=json.loads((out/'blind_stage_a_summary.json').read_text(encoding='utf-8'))
    if certified:
        gate='PASS_STAGE_A_RECURRENT_SHAPE_CLOCK_MESH_GAUGE_CERTIFIED'
    elif provisional:
        gate=('FAIL_STAGE_A_PROVISIONAL_CANDIDATES_NOT_MESH_GAUGE_INVARIANT'
              if bool(base.get('coverage_ok_for_global_fail',False))
              else 'INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE__PROVISIONAL_CANDIDATES_NOT_GAUGE_CERTIFIED')
    else:
        gate=base.get('primary_gate','INDETERMINATE_STAGE_A_INSUFFICIENT_VALID_COVERAGE')
    summary={'format':'SST-INTRINSIC-MODAL-STAGE-A-GAUGE-BLIND-2.1','n_provisional_candidates':len(provisional),'n_mesh_gauge_certified_candidates':len(certified),'carriers_with_mesh_gauge_certified_candidates':len(set(c['carrier_id'] for c in certified)),'gauge_rates':[float(cfg.get('mesh_redistribution_rate',4))*float(cfg.get('mesh_gauge_low_factor',.6)),float(cfg.get('mesh_redistribution_rate',4))*float(cfg.get('mesh_gauge_high_factor',1.4))],'carrier_identity_read':False,'primary_gate':gate}
    (out/'blind_stage_a_gauge_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary

def analyze_stage_b(work,cfg):
    work=Path(work); out=work/'analysis'; candidates=_load_stage_a_candidates(work); pairs=_pairs(work); result=[]
    for c in candidates:
        rr=pairs.get(c['pair_id'],[]); rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0)
        if not rp or not rm or not r0: continue
        branch_data={}; missing=False
        for branch in ('material','fixed'):
            fps=[_stage_b_file(work,branch,r) for r in (rp,rm,r0)]
            if not all(p.exists() for p in fps): missing=True; break
            branch_data[branch]=tuple(map(_load,fps))
        if missing: continue
        mf=np.load(work/c['mode_file'],allow_pickle=False); mode=np.asarray(mf['modes'][int(c['mode_index'])],float); center=np.asarray(mf['center'],float); ref=np.asarray(mf['reference'],float); w=mode_strain_weights(mode,ref)
        metrics={}
        for branch in ('material','fixed'):
            zp,zm,z0=branch_data[branch]; n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float)
            resp,sig=_response_for_channel(c['channel'],zp,zm,z0,float(cfg['probe_eps']),ref); resp=resp[:n]; sig=sig[:n]
            a=project(resp,np.asarray([mode]),center)[:,0]; s=sig@w
            actual=float(t[-1]); period=float(c.get('period') or np.nan); minobs=float(cfg.get('stage_b_min_periods_observed',1.25))*period if np.isfinite(period) else np.inf
            geometry_ok=bool(actual>=float(cfg.get('stage_b_discovery_time',1.0))+minobs and max(float(np.max(zp['ds_cv'])),float(np.max(zm['ds_cv'])),float(np.max(z0['ds_cv'])))<=float(cfg.get('stage_b_hard_ds_cv',.45)))
            delay=delayed_stretch_test(t,a,s,period,float(cfg.get('stage_b_discovery_time',1.0)),int(cfg.get('n_phase_nulls',31))) if geometry_ok else {}
            metrics[branch]={'geometry_ok':geometry_ok,'actual_t_final':actual,'max_ds_cv':float(max(np.max(zp['ds_cv']),np.max(zm['ds_cv']),np.max(z0['ds_cv']))),**delay}
        md=metrics['material']; fd=metrics['fixed']
        sb1=bool(md.get('geometry_ok') and abs(md.get('holdout_corr',0))>=float(cfg.get('gate_min_stretch_accel_corr',.35)) and md.get('phase_null_p',1)<=float(cfg.get('gate_max_phase_null_p',.05)))
        sb2=bool(sb1 and md.get('delay',0)>=2*float(np.median(np.diff(branch_data['material'][2]['t']))) and md.get('delay_advantage_abs_corr',-99)>=float(cfg.get('gate_min_delay_advantage',.08)))
        fixed_strength=abs(fd.get('holdout_corr',0)) if fd.get('geometry_ok') else 0.; material_strength=abs(md.get('holdout_corr',0)); sb3=bool(sb2 and (not fd.get('geometry_ok') or material_strength-fixed_strength>=float(cfg.get('gate_min_material_over_fixed_corr',.08))))
        result.append({**c,'stage_b_material_geometry_ok':md.get('geometry_ok',False),'stage_b_fixed_geometry_ok':fd.get('geometry_ok',False),**{f'material_{k}':v for k,v in md.items()},**{f'fixed_{k}':v for k,v in fd.items()},'SB1_stretch_coupling':sb1,'SB2_measured_delay_advantage':sb2,'SB3_material_core_specificity':sb3,'clock_mechanism_candidate':sb3})
    _savecsv(out/'blind_stage_b_results.csv',result); mech=[r for r in result if r['clock_mechanism_candidate']]; sa=len(candidates)
    if mech: gate='PASS_CANDIDATE_INTRINSIC_SWIRL_CLOCK_MECHANISM'
    elif sa: gate='PASS_STAGE_A_RECURRENCE__FAIL_OR_INDETERMINATE_STAGE_B_CAUSALITY'
    else:
        ga=out/'blind_stage_a_gauge_summary.json'; gate=json.loads(ga.read_text()).get('primary_gate') if ga.exists() else json.loads((out/'blind_stage_a_summary.json').read_text()).get('primary_gate')
    summary={'format':'SST-INTRINSIC-MODAL-CLOCK-BLIND-2.1','n_stage_a_candidates':sa,'n_stage_b_results':len(result),'n_clock_mechanism_candidates':len(mech),'carriers_with_clock_mechanism_candidates':len(set(r['carrier_id'] for r in mech)),'carrier_identity_read':False,'qhp_coordinate_used':False,'stage_a_basis_frozen_for_stage_b':True,'stage_a_mesh_gauge_certified_for_stage_b':True,'primary_gate':gate}
    (out/'blind_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary
