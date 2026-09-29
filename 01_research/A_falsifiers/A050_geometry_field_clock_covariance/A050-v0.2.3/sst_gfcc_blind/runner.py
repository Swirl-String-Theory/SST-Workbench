from pathlib import Path
import csv, hashlib, json, os, platform, sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
from .geometry import make_curve
from .filament import evolve_curve
from .persistence import modal_persistence_metrics, numerical_convergence
from .basin import load_direction_manifest, load_direction, perturb_base, measured_perturbation_rms, aggregate_amplitudes

ROOT=Path(__file__).resolve().parents[1]

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def write_json(path,obj):
    Path(path).write_text(json.dumps(_clean(obj),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')

def _clean(x):
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,(np.integer,int)): return int(x)
    if isinstance(x,(np.floating,float)):
        v=float(x); return v if np.isfinite(v) else None
    if isinstance(x,np.ndarray): return [_clean(v) for v in x.tolist()]
    if isinstance(x,dict): return {str(k):_clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_clean(v) for v in x]
    return x

def write_csv(path,rows):
    rows=list(rows); p=Path(path)
    if not rows: p.write_text('',encoding='utf-8'); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
        for r in rows:
            q={k:(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in r.items()}
            w.writerow(q)

def environment():
    return {'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'cpu_count':os.cpu_count()}

def _target_mean_frequency(pm,target):
    vals=[]
    for z in pm['checkpoints']:
        if z['checkpoint'] in (640,1024,1536,2048) and z['pass'] and z['selected_mode']==target and np.isfinite(z['frequency']): vals.append(float(z['frequency']))
    return float(np.mean(vals)) if vals else float('nan')

def _one_job(args):
    root,cfg,entry,eps=args
    base=make_curve(cfg['base_family'],int(cfg['curve_points']),seed=int(cfg['seed']))
    d=load_direction(root,entry)
    p0=perturb_base(base,d,float(eps))
    frames=evolve_curve(p0,float(cfg['core_ratio']),float(cfg['time_step']),int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    pm=modal_persistence_metrics(frames,float(cfg['time_step']),cfg['modal_persistence_gate'],cfg['kelvin_gate'])
    target=int(cfg['target_branch_mode'])
    return {
      'trajectory_id':f'E{int(round(float(eps)*1e6)):06d}_{entry["direction_id"]}',
      'direction_id':entry['direction_id'],'epsilon':float(eps),'direction_target_mode3_overlap':float(entry['target_mode3_overlap']),
      'measured_perturbation_rms':measured_perturbation_rms(p0,base),'persistence':pm,
      'strict_target_pass':bool(pm['pass'] and pm['persistent_mode']==target),
      'target_mean_frequency':_target_mean_frequency(pm,target)
    }

def _baseline(cfg):
    base=make_curve(cfg['base_family'],int(cfg['curve_points']),seed=int(cfg['seed']))
    frames=evolve_curve(base,float(cfg['core_ratio']),float(cfg['time_step']),int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    pm=modal_persistence_metrics(frames,float(cfg['time_step']),cfg['modal_persistence_gate'],cfg['kelvin_gate'])
    target=int(cfg['target_branch_mode'])
    return {'trajectory_id':'BASELINE','epsilon':0.0,'measured_perturbation_rms':0.0,'persistence':pm,'strict_target_pass':bool(pm['pass'] and pm['persistent_mode']==target),'target_mean_frequency':_target_mean_frequency(pm,target)}

def _cache_load(p):
    try: return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception: return None

def _core_assessment(cfg,baseline,agg):
    bcfg=cfg['basin_map']; target=int(cfg['target_branch_mode'])
    amap={round(float(a['epsilon']),8):a for a in agg}
    cores=[]
    for eps in bcfg['core_amplitudes']:
        a=amap.get(round(float(eps),8))
        support_ok=bool(a and a['strict_target_support']>=int(bcfg['minimum_core_support']))
        freq_ok=bool(a and a['cross_direction_frequency_cv']<=float(bcfg['cross_direction_frequency_cv_max']))
        cores.append({'epsilon':float(eps),'support_ok':support_ok,'frequency_ok':freq_ok,'row':a})
    core_support=all(x['support_ok'] for x in cores)
    freq_robust=all(x['frequency_ok'] for x in cores)
    baseline_ok=bool(baseline['strict_target_pass'])
    smallest=amap.get(round(float(min(e for e in bcfg['amplitude_ladder'] if e>0)),8))
    if not baseline_ok:
        status='BASELINE_M3_NOT_PERSISTENT'
    elif smallest and smallest['strict_target_support']==0:
        status='ISOLATED_M3_TRAJECTORY_BEHAVIOR'
    elif not core_support:
        status='NARROW_OR_ANISOTROPIC_M3_BASIN'
    elif not freq_robust:
        status='LOCAL_M3_BASIN_FREQUENCY_NONROBUST'
    else:
        status='FINITE_RADIUS_M3_BASIN_SUPPORTED'
    return {'status':status,'baseline_ok':baseline_ok,'core_support':core_support,'frequency_robust':freq_robust,'core_rows':cores}

def run_campaign(config_path,out_dir,workers=None,resume=True):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8'))
    if cfg.get('analysis_stage')!='post_confirmatory_reveal_diagnostic': raise RuntimeError('wrong analysis stage')
    parent=json.loads((ROOT/cfg['provenance']['parent_evidence']).read_text(encoding='utf-8'))
    if parent['parent_primary_verdict']!='MODAL_PERSISTENCE_NOT_REPRODUCED': raise RuntimeError('unexpected parent verdict')
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); cache=out/cfg['execution']['cache_subdir']; cache.mkdir(exist_ok=True)
    write_json(out/'config_used.json',cfg); write_json(out/'environment.json',environment()); write_json(out/'parent_provenance_used.json',parent)
    manifest=load_direction_manifest(ROOT,cfg['basin_map']['direction_manifest'])
    if len(manifest['entries'])!=int(cfg['basin_map']['direction_count']): raise RuntimeError('direction count mismatch')
    # Baseline cache
    bp=cache/'BASELINE.json'; baseline=_cache_load(bp) if resume else None
    if baseline is None:
        baseline=_baseline(cfg); write_json(bp,baseline)
    jobs=[]; rows=[]
    for eps in cfg['basin_map']['amplitude_ladder']:
        if float(eps)==0.0: continue
        for e in manifest['entries']:
            tid=f'E{int(round(float(eps)*1e6)):06d}_{e["direction_id"]}'
            cp=cache/f'{tid}.json'; old=_cache_load(cp) if resume else None
            if old is not None: rows.append(old)
            else: jobs.append((str(ROOT),cfg,e,float(eps)))
    nworkers=int(workers or cfg['execution']['default_workers']); nworkers=max(1,nworkers)
    if jobs:
        if nworkers==1:
            for j in jobs:
                r=_one_job(j); write_json(cache/f'{r["trajectory_id"]}.json',r); rows.append(r); print(f'[v0.2.3] {r["trajectory_id"]} done',flush=True)
        else:
            with ProcessPoolExecutor(max_workers=nworkers) as ex:
                fut={ex.submit(_one_job,j):j for j in jobs}
                for f in as_completed(fut):
                    r=f.result(); write_json(cache/f'{r["trajectory_id"]}.json',r); rows.append(r); print(f'[v0.2.3] {r["trajectory_id"]} done',flush=True)
    rows=sorted(rows,key=lambda r:(float(r['epsilon']),r['direction_id']))
    agg=aggregate_amplitudes(rows,int(cfg['target_branch_mode']))
    assess=_core_assessment(cfg,baseline,agg)
    conv=None
    if assess['status']=='FINITE_RADIUS_M3_BASIN_SUPPORTED' and cfg['numerical_convergence_gate']['enabled']:
        rep_eps=float(cfg['numerical_convergence_gate']['representative_amplitude'])
        members=[r for r in rows if abs(float(r['epsilon'])-rep_eps)<1e-15 and r['strict_target_pass']]
        members=sorted(members,key=lambda r:r['direction_id'])
        if members:
            ent=next(e for e in manifest['entries'] if e['direction_id']==members[0]['direction_id'])
            base=make_curve(cfg['base_family'],int(cfg['curve_points']),seed=int(cfg['seed'])); d=load_direction(ROOT,ent); p0=perturb_base(base,d,rep_eps)
            conv=numerical_convergence(p0,int(cfg['target_branch_mode']),float(cfg['core_ratio']),int(cfg['reparameterize_every']),int(cfg['field_chunk']),cfg['numerical_convergence_gate'],cfg['kelvin_gate'])
            conv['direction_id']=ent['direction_id']; conv['epsilon']=rep_eps
    if assess['status']=='FINITE_RADIUS_M3_BASIN_SUPPORTED' and conv is not None and not conv['pass']:
        verdict='FINITE_RADIUS_M3_BASIN_NONCONVERGENT'
    else:
        verdict=assess['status']
    result={
      'stage':'post_confirmatory_diagnostic_complete','version':'v0.2.3','verdict':verdict,
      'parent_verdict_locked':parent['parent_primary_verdict'],'target':{'family':cfg['base_family'],'branch_mode':int(cfg['target_branch_mode'])},
      'baseline':baseline,'basin_assessment':assess,'amplitude_summary':agg,'trajectories':rows,'numerical_convergence':conv,
      'limitations':[
        'v0.2.3 was selected after revealing v0.2.2 and is a post-confirmatory mechanism diagnostic, not an independent confirmation.',
        'The v0.2.2 verdict remains MODAL_PERSISTENCE_NOT_REPRODUCED regardless of the v0.2.3 outcome.',
        'The perturbation directions are a fixed finite sample of a transverse Fourier subspace, not the full infinite-dimensional neighborhood.',
        'The base curve is generated dimensionless G0002 geometry rather than production PKLSA/Ridgerunner geometry.',
        'No Floquet/RPO inference is made in v0.2.3.',
        'No absolute SST physical scale or target constant is used.'
      ]
    }
    write_json(out/'diagnostic_results.json',result)
    # Flat outputs
    trows=[]; cprows=[]
    for r in rows:
        p=r['persistence']; trows.append({'trajectory_id':r['trajectory_id'],'direction_id':r['direction_id'],'epsilon':r['epsilon'],'measured_perturbation_rms':r['measured_perturbation_rms'],'direction_target_mode3_overlap':r['direction_target_mode3_overlap'],'strict_m3_pass':r['strict_target_pass'],'persistent_mode':p['persistent_mode'],'qualified_late_checkpoints':p['qualified_late_checkpoints'],'frequency_cv':p['frequency_cv'],'final_checkpoint_qualified':p['final_checkpoint_qualified'],'mode_switch_count':p['mode_switch_count'],'target_mean_frequency':r['target_mean_frequency']})
        for z in p['checkpoints']:
            cprows.append({'trajectory_id':r['trajectory_id'],'direction_id':r['direction_id'],'epsilon':r['epsilon'],'checkpoint':z['checkpoint'],'pass':z['pass'],'selected_mode':z['selected_mode'],'dominant_fraction':z['dominant_fraction'],'phase_r2':z['phase_r2'],'phase_cycles':z['phase_cycles'],'frequency':z['frequency']})
    arows=[]
    for a in agg: arows.append({**a,'persistent_mode_histogram':json.dumps(a['persistent_mode_histogram'],sort_keys=True)})
    write_csv(out/'basin_trajectories.csv',trows); write_csv(out/'basin_checkpoints.csv',cprows); write_csv(out/'basin_amplitude_summary.csv',arows)
    if conv is not None: write_json(out/'modal_numerical_convergence.json',conv)
    digest=sha256(out/'diagnostic_results.json'); (out/'diagnostic_results.sha256').write_text(digest+'  diagnostic_results.json\n',encoding='utf-8')
    return result
