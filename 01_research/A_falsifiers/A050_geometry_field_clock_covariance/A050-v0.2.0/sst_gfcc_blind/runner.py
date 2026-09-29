from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .geometry import make_curve, curve_metrics
from .filament import evolve_curve
from .field import normalized_velocity_on_grid, pressure_like, divergence_rms, gradient_rms
from .analysis import variance_scaling_scalar, variance_scaling_vector, shuffled_scaling, fit_power, radial_autocorrelation, smooth_periodic, temporal_integrated_variance, fit_temporal
from .temporal import memory_metrics, shuffled_memory_null
from .modes import kelvin_metrics
from .floquet import floquet_gate
from .io import write_json, write_csv, environment, sha256


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


def run_family(code, cfg, grid_override=None, temporal=True):
    ncurve=int(cfg['curve_points']); grid=int(grid_override or cfg['grid_n']); core=float(cfg['core_ratio'])
    p0=make_curve(code,ncurve,int(cfg['seed']))
    frames=evolve_curve(p0,core,float(cfg['time_step']),int(cfg['evolution_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    inds=_sample_indices(cfg['evolution_steps'],cfg['sample_every'])
    radii=[r for r in map(int,cfg['window_radii_cells']) if r<grid//2]
    rng=np.random.default_rng(int(cfg['seed'])+sum(map(ord,code))+grid)
    rows=[]; vp=[]; vu=[]; vn=[]; divrat=[]; corr=[]; probe_series=[]
    probes=rng.integers(0,grid,size=(int(cfg['probe_count']),3))
    for s in inds:
        curve=frames[s]
        u,dx=normalized_velocity_on_grid(curve,grid,float(cfg['box_half_extent']),core,int(cfg['field_chunk']))
        pr,src=pressure_like(u,dx)
        d=divergence_rms(u,dx); g=gradient_rms(u,dx); ratio=d/max(g,1e-30)
        pscale=variance_scaling_scalar(pr,radii); uscale=variance_scaling_vector(u,radii); nscale=shuffled_scaling(pr,radii,int(cfg['null_shuffle_repeats']),rng)
        _,cl=radial_autocorrelation(pr)
        vp.append(pscale); vu.append(uscale); vn.append(nscale); divrat.append(ratio); corr.append(cl)
        if temporal:
            sm=smooth_periodic(pr,int(cfg['probe_radius_cells']))
            probe_series.append(np.asarray([sm[tuple(ix)] for ix in probes],float))
        rows.append({'family':code,'grid_n':grid,'step':s,'divergence_ratio':ratio,'pressure_variance':float(np.var(pr)),'source_variance':float(np.var(src)),'corr_length_cells':cl})
    vp=np.mean(np.asarray(vp),axis=0); vu=np.mean(np.asarray(vu),axis=0); vn=np.mean(np.asarray(vn),axis=0)
    fp=fit_power(radii,vp,int(cfg['fit_min_radius_cells'])); fu=fit_power(radii,vu,int(cfg['fit_min_radius_cells'])); fn=fit_power(radii,vn,int(cfg['fit_min_radius_cells']))
    tf={'exponent':float('nan'),'r2':float('nan')}; mem={}; memnull={}; tv_t=[]; tv_v=[]
    if temporal and len(probe_series)>=4:
        arr=np.asarray(probe_series); eff_dt=float(cfg['time_step'])*int(cfg['sample_every'])
        tv_t,tv_v=temporal_integrated_variance(arr,eff_dt); tf=fit_temporal(tv_t,tv_v)
        tcfg=cfg['temporal_memory_gate']; mem=memory_metrics(arr,eff_dt,max_lag=int(tcfg['max_lag_samples']))
        memnull=shuffled_memory_null(arr,eff_dt,int(tcfg['shuffle_repeats']),rng,max_lag=int(tcfg['max_lag_samples']))
        ratio=float(mem['memory_steps']/max(memnull['memory_steps_mean'],1e-12)) if np.isfinite(mem['memory_steps']) else float('nan')
        lag_excess=float(mem['lag1']-memnull['lag1_mean']) if np.isfinite(mem['lag1']) else float('nan')
        passed=bool(np.isfinite(ratio) and np.isfinite(lag_excess) and ratio>=float(tcfg['memory_ratio_min']) and lag_excess>=float(tcfg['lag1_excess_min']))
        mem.update({'null':memnull,'memory_ratio_to_null':ratio,'lag1_excess':lag_excess,'pass':passed,'status':'TEMPORAL_MEMORY_RESOLVED' if passed else 'TEMPORAL_MEMORY_NOT_RESOLVED'})
    kcfg=cfg['kelvin_gate']
    km=kelvin_metrics(frames,float(cfg['time_step']),kcfg)
    return {
      'family':code,'grid_n':grid,'geometry':curve_metrics(p0),'snapshot_rows':rows,
      'radii':radii,'pressure_scaling':vp.tolist(),'velocity_scaling':vu.tolist(),'null_scaling':vn.tolist(),
      'pressure_fit':fp,'velocity_fit':fu,'null_fit':fn,
      'mean_divergence_ratio':float(np.mean(divrat)),'mean_corr_length_cells':float(np.nanmean(corr)),
      'temporal_fit':tf,'temporal_t':np.asarray(tv_t).tolist(),'temporal_variance':np.asarray(tv_v).tolist(),
      'memory_gate':mem,'kelvin_gate':km,
    }


def run_campaign(config_path, out_dir):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if cfg.get('blind') is not True: raise RuntimeError('blind flag must be true')
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    write_json(out/'config_used.json',cfg); write_json(out/'environment.json',environment())
    fam=[run_family(code,cfg) for code in cfg['families']]
    res=[]; rcfg=cfg.get('resolution_check',{})
    if rcfg.get('enabled'):
        for gn in rcfg['grid_values']:
            rr=run_family(rcfg['family'],cfg,grid_override=int(gn),temporal=False)
            res.append({'grid_n':int(gn),'pressure_exponent':rr['pressure_fit']['exponent'],'pressure_r2':rr['pressure_fit']['r2']})
    spatial_good=[]
    for r in fam:
        fp=r['pressure_fit']; fn=r['null_fit']
        ok=(np.isfinite(fp['exponent']) and np.isfinite(fn['exponent']) and fp['r2']>=float(cfg['power_fit_r2_min']) and (fn['exponent']-fp['exponent'])>=float(cfg['null_gap_min']))
        spatial_good.append(bool(ok))
    res_ok=True; res_delta=None
    if len(res)>=2:
        vals=[x['pressure_exponent'] for x in res if x['pressure_exponent'] is not None and np.isfinite(x['pressure_exponent'])]
        if len(vals)>=2:
            res_delta=float(max(vals)-min(vals)); res_ok=res_delta<=float(rcfg['max_exponent_delta'])
        else: res_ok=False
    div_ok=all(r['mean_divergence_ratio']<1e-10 for r in fam)
    spatial_count=sum(spatial_good)
    memory_count=sum(bool(r.get('memory_gate',{}).get('pass',False)) for r in fam)
    kelvin_count=sum(bool(r.get('kelvin_gate',{}).get('pass',False)) for r in fam)
    fcfg=cfg['floquet_gate']; fcode=fcfg['family']; p0=make_curve(fcode,int(cfg['curve_points']),int(cfg['seed']))
    fg=floquet_gate(p0,float(cfg['core_ratio']),float(cfg['time_step']),int(fcfg['search_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']),fcfg)
    spatial_ok=spatial_count>=int(cfg['minimum_spatial_families'])
    memory_ok=memory_count>=int(cfg['temporal_memory_gate']['minimum_families'])
    kelvin_ok=kelvin_count>=int(cfg['kelvin_gate']['minimum_families'])
    if not div_ok or not res_ok:
        verdict='NUMERICAL_QUALIFICATION_FAILED'
    elif not spatial_ok:
        verdict='CORRELATED_CLOSURE_SCALING_NOT_DETECTED'
    elif not memory_ok:
        verdict='TEMPORAL_MEMORY_NOT_DETECTED'
    elif not kelvin_ok:
        verdict='TEMPORAL_MEMORY_DETECTED_KELVIN_NOT_RESOLVED'
    elif fg.get('resolved'):
        verdict='STRUCTURED_MEMORY_KELVIN_FLOQUET_RESOLVED'
    else:
        verdict='STRUCTURED_MEMORY_KELVIN_DETECTED_FLOQUET_INDETERMINATE'
    summary={
      'stage':'blind_complete','blind':True,'verdict':verdict,
      'spatial_gate':{'pass':spatial_ok,'qualified_family_count':int(spatial_count),'family_count':len(fam)},
      'temporal_memory_gate':{'pass':memory_ok,'qualified_family_count':int(memory_count),'family_count':len(fam)},
      'kelvin_gate':{'pass':kelvin_ok,'qualified_family_count':int(kelvin_count),'family_count':len(fam)},
      'floquet_gate':fg,
      'divergence_gate':bool(div_ok),'resolution_gate':bool(res_ok),'resolution_exponent_span':res_delta,
      'families':fam,'resolution_check':res,
      'limitations':[
        'Reference campaign uses generated dimensionless closed curves rather than production geometry files.',
        'The scalar closure is solved on a periodic finite grid and can be box-limited at large averaging windows.',
        'The temporal-memory channel uses a finite set of spatial probes and a finite trajectory.',
        'The transverse-mode gate detects coherent filament modes but does not by itself identify a material wave speed.',
        'The Floquet gate is reported as indeterminate unless a nontrivial return is resolved before any multiplier is interpreted.',
        'No absolute physical scale or theory-specific target value is used by the blind verdict.'
      ]
    }
    summary=_clean_num(summary); write_json(out/'blind_results.json',summary)
    srows=[]; grow=[]; snap=[]; mrows=[]; krows=[]
    for r in fam:
        srows.append({'family':r['family'],'grid_n':r['grid_n'],'pressure_exponent':r['pressure_fit']['exponent'],'pressure_r2':r['pressure_fit']['r2'],'velocity_exponent':r['velocity_fit']['exponent'],'velocity_r2':r['velocity_fit']['r2'],'null_exponent':r['null_fit']['exponent'],'null_r2':r['null_fit']['r2'],'temporal_exponent':r['temporal_fit']['exponent'],'temporal_r2':r['temporal_fit']['r2'],'mean_divergence_ratio':r['mean_divergence_ratio'],'corr_length_cells':r['mean_corr_length_cells']})
        grow.append({'family':r['family'],**r['geometry']}); snap.extend(r['snapshot_rows'])
        mg=r.get('memory_gate',{}); mrows.append({'family':r['family'],'status':mg.get('status'),'pass':mg.get('pass'),'lag1':mg.get('lag1'),'lag1_excess':mg.get('lag1_excess'),'memory_steps':mg.get('memory_steps'),'memory_ratio_to_null':mg.get('memory_ratio_to_null'),'null_memory_steps':mg.get('null',{}).get('memory_steps_mean')})
        kg=r.get('kelvin_gate',{}); krows.append({'family':r['family'],'status':kg.get('status'),'pass':kg.get('pass'),'selected_mode':kg.get('selected_mode'),'dominant_fraction':kg.get('dominant_fraction'),'phase_r2':kg.get('phase_r2'),'phase_cycles':kg.get('phase_cycles'),'frequency':kg.get('frequency'),'amplitude_rms':kg.get('amplitude_rms')})
    write_csv(out/'scaling_results.csv',srows); write_csv(out/'geometry_metrics.csv',grow); write_csv(out/'snapshot_diagnostics.csv',snap); write_csv(out/'resolution_results.csv',res); write_csv(out/'temporal_memory_results.csv',mrows); write_csv(out/'kelvin_results.csv',krows)
    write_json(out/'floquet_results.json',fg)
    digest=sha256(out/'blind_results.json'); (out/'blind_results.sha256').write_text(digest+'  blind_results.json\n',encoding='utf-8')
    return summary
