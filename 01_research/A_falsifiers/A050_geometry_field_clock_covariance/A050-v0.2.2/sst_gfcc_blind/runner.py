from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .geometry import make_curve, curve_metrics
from .filament import evolve_curve
from .field import normalized_velocity_on_grid, pressure_like, divergence_rms, gradient_rms
from .analysis import variance_scaling_scalar, variance_scaling_vector, shuffled_scaling, fit_power, radial_autocorrelation, smooth_periodic, temporal_integrated_variance, fit_temporal
from .temporal import memory_metrics, shuffled_memory_null, memory_convergence
from .modes import kelvin_metrics
from .persistence import load_manifest, load_carrier, modal_persistence_metrics, aggregate_groups, numerical_convergence
from .io import write_json, write_csv, environment, sha256

ROOT=Path(__file__).resolve().parents[1]


def _clean_num(x):
    if isinstance(x, dict): return {k:_clean_num(v) for k,v in x.items()}
    if isinstance(x, list): return [_clean_num(v) for v in x]
    if isinstance(x, (np.floating,float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,int)): return int(x)
    if isinstance(x, (np.bool_,bool)): return bool(x)
    return x


def _sample_indices(total_steps, every):
    a=list(range(0,int(total_steps)+1,int(every)))
    if a[-1]!=int(total_steps): a.append(int(total_steps))
    return a


def _legacy_memory_gate(arr, eff_dt, cfg, rng):
    mem=memory_metrics(arr,eff_dt,max_lag=int(cfg['max_lag_samples']))
    null=shuffled_memory_null(arr,eff_dt,int(cfg['shuffle_repeats']),rng,max_lag=int(cfg['max_lag_samples']))
    ratio=float(mem['memory_steps']/max(null['memory_steps_mean'],1e-12)) if np.isfinite(mem['memory_steps']) else float('nan')
    lag_excess=float(mem['lag1']-null['lag1_mean']) if np.isfinite(mem['lag1']) else float('nan')
    passed=bool(np.isfinite(ratio) and np.isfinite(lag_excess) and ratio>=float(cfg['memory_ratio_min']) and lag_excess>=float(cfg['lag1_excess_min']))
    return {**mem,'null':null,'memory_ratio_to_null':ratio,'lag1_excess':lag_excess,'pass':passed,'status':'TEMPORAL_MEMORY_RESOLVED' if passed else 'TEMPORAL_MEMORY_NOT_RESOLVED'}


def run_base_family(code, cfg, grid_override=None, temporal=True):
    ncurve=int(cfg['curve_points']); grid=int(grid_override or cfg['grid_n']); core=float(cfg['core_ratio'])
    p0=make_curve(code,ncurve,int(cfg['seed']))
    max_steps=max(int(cfg['modal_persistence_steps']),int(cfg['temporal_memory_steps']),int(cfg['spatial_gate_steps'])) if temporal else int(cfg['spatial_gate_steps'])
    frames=evolve_curve(p0,core,float(cfg['time_step']),max_steps,int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    spatial_inds=set(_sample_indices(int(cfg['spatial_gate_steps']),cfg['sample_every']))
    memory_inds=_sample_indices(int(cfg['temporal_memory_steps']),cfg['sample_every']) if temporal else sorted(spatial_inds)
    radii=[r for r in map(int,cfg['window_radii_cells']) if r<grid//2]
    rng=np.random.default_rng(int(cfg['seed'])+sum(map(ord,code))+grid)
    rows=[]; vp=[]; vu=[]; vn=[]; divrat=[]; corr=[]; probe_series=[]; probe_steps=[]
    probes=rng.integers(0,grid,size=(int(cfg['probe_count']),3))
    for s in memory_inds:
        curve=frames[s]
        u,dx=normalized_velocity_on_grid(curve,grid,float(cfg['box_half_extent']),core,int(cfg['field_chunk']))
        pr,src=pressure_like(u,dx)
        if temporal:
            sm=smooth_periodic(pr,int(cfg['probe_radius_cells']))
            probe_series.append(np.asarray([sm[tuple(ix)] for ix in probes],float)); probe_steps.append(int(s))
        if s in spatial_inds:
            d=divergence_rms(u,dx); g=gradient_rms(u,dx); ratio=d/max(g,1e-30)
            pscale=variance_scaling_scalar(pr,radii); uscale=variance_scaling_vector(u,radii); nscale=shuffled_scaling(pr,radii,int(cfg['null_shuffle_repeats']),rng)
            _,cl=radial_autocorrelation(pr)
            vp.append(pscale); vu.append(uscale); vn.append(nscale); divrat.append(ratio); corr.append(cl)
            rows.append({'family':code,'grid_n':grid,'step':s,'divergence_ratio':ratio,'pressure_variance':float(np.var(pr)),'source_variance':float(np.var(src)),'corr_length_cells':cl})
    vp=np.mean(np.asarray(vp),axis=0); vu=np.mean(np.asarray(vu),axis=0); vn=np.mean(np.asarray(vn),axis=0)
    fp=fit_power(radii,vp,int(cfg['fit_min_radius_cells'])); fu=fit_power(radii,vu,int(cfg['fit_min_radius_cells'])); fn=fit_power(radii,vn,int(cfg['fit_min_radius_cells']))
    tf={'exponent':float('nan'),'r2':float('nan')}; mem={}; memconv={}; tv_t=[]; tv_v=[]
    if temporal and len(probe_series)>=4:
        arr=np.asarray(probe_series); eff_dt=float(cfg['time_step'])*int(cfg['sample_every'])
        tv_t,tv_v=temporal_integrated_variance(arr,eff_dt); tf=fit_temporal(tv_t,tv_v)
        mem=_legacy_memory_gate(arr,eff_dt,cfg['temporal_memory_gate'],rng)
        memconv=memory_convergence(arr,probe_steps,eff_dt,cfg['temporal_memory_convergence_gate'],cfg['temporal_memory_gate'],rng)
    kg=kelvin_metrics(frames,float(cfg['time_step']),cfg['kelvin_gate']) if temporal else {}
    return {
      'family':code,'grid_n':grid,'geometry':curve_metrics(p0),'snapshot_rows':rows,
      'radii':radii,'pressure_scaling':vp.tolist(),'velocity_scaling':vu.tolist(),'null_scaling':vn.tolist(),
      'pressure_fit':fp,'velocity_fit':fu,'null_fit':fn,
      'mean_divergence_ratio':float(np.mean(divrat)),'mean_corr_length_cells':float(np.nanmean(corr)),
      'temporal_fit':tf,'temporal_t':np.asarray(tv_t).tolist(),'temporal_variance':np.asarray(tv_v).tolist(),
      'memory_gate':mem,'memory_convergence':memconv,'modal_diagnostic':kg,
    }


def run_holdouts(cfg):
    manifest=load_manifest(ROOT,cfg['modal_persistence_gate']['holdout_manifest'])
    results=[]
    for entry in manifest['entries']:
        p0=load_carrier(ROOT,entry)
        frames=evolve_curve(p0,float(cfg['core_ratio']),float(cfg['time_step']),int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
        pm=modal_persistence_metrics(frames,float(cfg['time_step']),cfg['modal_persistence_gate'],cfg['kelvin_gate'])
        results.append({'carrier_id':entry['carrier_id'],'group_id':entry['group_id'],'input_sha256':entry['sha256'],'persistence':pm})
    groups=aggregate_groups(results,cfg['modal_persistence_gate'])
    return manifest,results,groups


def run_modal_convergence(cfg, manifest, carriers, groups):
    byid={e['carrier_id']:e for e in manifest['entries']}
    out=[]
    for g in groups:
        if not g['pass']:
            continue
        candidates=sorted(g['supporting_carrier_ids'])
        cid=candidates[0]
        entry=byid[cid]; p0=load_carrier(ROOT,entry)
        conv=numerical_convergence(p0,int(g['branch_mode']),float(cfg['core_ratio']),int(cfg['reparameterize_every']),int(cfg['field_chunk']),cfg['modal_numerical_convergence_gate'],cfg['kelvin_gate'])
        out.append({'group_id':g['group_id'],'carrier_id':cid,**conv})
    return out


def run_campaign(config_path, out_dir):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if cfg.get('blind') is not True: raise RuntimeError('blind flag must be true')
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    write_json(out/'config_used.json',cfg); write_json(out/'environment.json',environment())
    fam=[run_base_family(code,cfg) for code in cfg['families']]
    res=[]; rcfg=cfg.get('resolution_check',{})
    if rcfg.get('enabled'):
        for gn in rcfg['grid_values']:
            rr=run_base_family(rcfg['family'],cfg,grid_override=int(gn),temporal=False)
            res.append({'grid_n':int(gn),'pressure_exponent':rr['pressure_fit']['exponent'],'pressure_r2':rr['pressure_fit']['r2']})
    spatial_good=[]
    for r in fam:
        fp=r['pressure_fit']; fn=r['null_fit']
        ok=(np.isfinite(fp['exponent']) and np.isfinite(fn['exponent']) and fp['r2']>=float(cfg['power_fit_r2_min']) and (fn['exponent']-fp['exponent'])>=float(cfg['null_gap_min']))
        spatial_good.append(bool(ok))
    vals=[x['pressure_exponent'] for x in res if x['pressure_exponent'] is not None and np.isfinite(x['pressure_exponent'])]
    res_delta=float(max(vals)-min(vals)) if len(vals)>=2 else None
    res_ok=bool(res_delta is not None and res_delta<=float(rcfg['max_exponent_delta'])) if rcfg.get('enabled') else True
    div_ok=all(r['mean_divergence_ratio']<1e-10 for r in fam)
    spatial_count=sum(spatial_good); spatial_ok=spatial_count>=int(cfg['minimum_spatial_families'])
    memory_present_count=sum(bool(r.get('memory_convergence',{}).get('present_final_two',False)) for r in fam)
    memory_converged_count=sum(bool(r.get('memory_convergence',{}).get('converged',False)) for r in fam)
    memory_present=memory_present_count>=int(cfg['temporal_memory_gate']['minimum_families'])
    memory_converged=memory_converged_count>=int(cfg['temporal_memory_convergence_gate']['minimum_converged_families'])
    manifest,carriers,groups=run_holdouts(cfg)
    confirmed=[g for g in groups if g['pass']]
    modal_reproduced=len(confirmed)>=int(cfg['modal_persistence_gate']['minimum_confirmed_groups'])
    conv=run_modal_convergence(cfg,manifest,carriers,groups) if modal_reproduced and cfg['modal_numerical_convergence_gate']['enabled'] else []
    conv_groups={z['group_id']:z for z in conv}
    qualified_groups=[g for g in confirmed if conv_groups.get(g['group_id'],{}).get('pass',False)] if cfg['modal_numerical_convergence_gate']['enabled'] else confirmed
    modal_converged=len(qualified_groups)>=int(cfg['modal_persistence_gate']['minimum_confirmed_groups'])
    if not div_ok or not res_ok or not spatial_ok:
        verdict='NUMERICAL_QUALIFICATION_FAILED'
    elif not memory_present:
        verdict='TEMPORAL_MEMORY_NOT_REPRODUCED'
    elif not memory_converged:
        verdict='TEMPORAL_MEMORY_PRESENT_NOT_CONVERGED'
    elif not modal_reproduced:
        verdict='MODAL_PERSISTENCE_NOT_REPRODUCED'
    elif not modal_converged:
        verdict='MODAL_PERSISTENCE_NONCONVERGENT'
    else:
        verdict='STRUCTURED_MEMORY_AND_MODAL_PERSISTENCE_CONFIRMED'
    summary={
      'stage':'blind_complete','blind':True,'version':'v0.2.2','verdict':verdict,
      'spatial_gate':{'pass':spatial_ok,'qualified_family_count':int(spatial_count),'family_count':len(fam)},
      'temporal_memory_gate':{'present':memory_present,'present_family_count':int(memory_present_count),'converged':memory_converged,'converged_family_count':int(memory_converged_count),'family_count':len(fam)},
      'modal_persistence_gate':{'reproduced':modal_reproduced,'numerically_converged':modal_converged,'confirmed_group_count':len(confirmed),'qualified_confirmed_group_count':len(qualified_groups),'group_count':len(groups)},
      'floquet_policy':cfg['floquet_policy'],
      'divergence_gate':bool(div_ok),'resolution_gate':bool(res_ok),'resolution_exponent_span':res_delta,
      'families':fam,'resolution_check':res,'holdout_groups':groups,'holdout_carriers':carriers,'modal_numerical_convergence':conv,
      'limitations':[
        'Reference campaign uses generated dimensionless closed curves and pre-generated blinded perturbation carriers rather than production geometry files.',
        'Holdout groups are anonymous during the blind run; interpretation of geometry identity is reveal-only.',
        'Temporal-memory convergence is estimated from a finite pressure-field probe ensemble and finite nested horizons.',
        'The phase-randomized surrogate is diagnostic only because preserving a power spectrum also preserves two-point autocorrelation structure.',
        'The transverse modal gate establishes persistence of a coherent filament mode, not an absolute material wave speed.',
        'Floquet/RPO analysis is intentionally inactive in v0.2.2 because v0.2.1 did not resolve a preregistered recurrence.',
        'No absolute physical scale or theory-specific target value is used by the blind verdict.'
      ]
    }
    summary=_clean_num(summary); write_json(out/'blind_results.json',summary)
    srows=[]; grow=[]; snap=[]; mrows=[]; krows=[]; mcrows=[]; pcrows=[]; pgrows=[]; ncrows=[]
    for r in fam:
        srows.append({'family':r['family'],'grid_n':r['grid_n'],'pressure_exponent':r['pressure_fit']['exponent'],'pressure_r2':r['pressure_fit']['r2'],'velocity_exponent':r['velocity_fit']['exponent'],'velocity_r2':r['velocity_fit']['r2'],'null_exponent':r['null_fit']['exponent'],'null_r2':r['null_fit']['r2'],'temporal_exponent':r['temporal_fit']['exponent'],'temporal_r2':r['temporal_fit']['r2'],'mean_divergence_ratio':r['mean_divergence_ratio'],'corr_length_cells':r['mean_corr_length_cells']})
        grow.append({'family':r['family'],**r['geometry']}); snap.extend(r['snapshot_rows'])
        mg=r.get('memory_gate',{}); mrows.append({'family':r['family'],'status':mg.get('status'),'pass':mg.get('pass'),'memory_steps':mg.get('memory_steps'),'memory_ratio_to_null':mg.get('memory_ratio_to_null'),'lag1_excess':mg.get('lag1_excess')})
        cv=r.get('memory_convergence',{}); mcrows.append({'family':r['family'],'status':cv.get('status'),'present_final_two':cv.get('present_final_two'),'converged':cv.get('converged'),'final_relative_change':cv.get('final_relative_change'),'final_bootstrap_ci_overlap':cv.get('final_bootstrap_ci_overlap')})
        kg=r.get('modal_diagnostic',{}); krows.append({'family':r['family'],'status':kg.get('status'),'pass':kg.get('pass'),'selected_mode':kg.get('selected_mode'),'dominant_fraction':kg.get('dominant_fraction'),'phase_r2':kg.get('phase_r2'),'phase_cycles':kg.get('phase_cycles'),'frequency':kg.get('frequency')})
    for c in carriers:
        p=c['persistence']; pcrows.append({'carrier_id':c['carrier_id'],'group_id':c['group_id'],'status':p['status'],'pass':p['pass'],'persistent_mode':p['persistent_mode'],'qualified_late_checkpoints':p['qualified_late_checkpoints'],'frequency_cv':p['frequency_cv'],'final_checkpoint_qualified':p['final_checkpoint_qualified'],'mode_switch_count':p['mode_switch_count']})
    pgrows=[{k:v for k,v in g.items() if k!='supporting_carrier_ids'} for g in groups]
    for z in conv:
        ncrows.append({'group_id':z['group_id'],'carrier_id':z['carrier_id'],'status':z['status'],'pass':z['pass'],'base_mode':z['base_mode'],'resolution_frequency_relative_span':z['resolution_frequency_relative_span'],'timestep_frequency_relative_span':z['timestep_frequency_relative_span']})
    write_csv(out/'scaling_results.csv',srows); write_csv(out/'geometry_metrics.csv',grow); write_csv(out/'snapshot_diagnostics.csv',snap); write_csv(out/'resolution_results.csv',res)
    write_csv(out/'temporal_memory_results.csv',mrows); write_csv(out/'temporal_memory_convergence.csv',mcrows); write_csv(out/'modal_diagnostics.csv',krows)
    write_csv(out/'modal_persistence_carriers.csv',pcrows); write_csv(out/'modal_persistence_groups.csv',pgrows); write_csv(out/'modal_numerical_convergence.csv',ncrows)
    digest=sha256(out/'blind_results.json'); (out/'blind_results.sha256').write_text(digest+'  blind_results.json\n',encoding='utf-8')
    return summary
