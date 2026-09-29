from pathlib import Path
import json, hashlib
import numpy as np
from .filament import evolve_curve
from .geometry import resample_closed
from .modes import kelvin_metrics, transverse_mode_series, kelvin_metrics_from_series


def load_manifest(root, relpath):
    p=Path(root)/relpath
    return json.loads(p.read_text(encoding='utf-8'))


def load_carrier(root, entry):
    p=Path(root)/'data'/entry['file'] if not str(entry['file']).startswith('data/') else Path(root)/entry['file']
    if not p.exists():
        p=Path(root)/'data'/Path(entry['file']).name if 'holdouts_blind' not in str(p) else p
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=entry['sha256']:
        raise RuntimeError(f'holdout hash mismatch: {entry["carrier_id"]}')
    return np.asarray(np.load(p)['points'],float)


def modal_persistence_metrics(frames, dt, cfg, legacy_cfg):
    # Compute the aligned transverse Fourier series once over the full trajectory.
    # Nested checkpoint metrics are then exact prefix reductions of the same series;
    # this is mathematically equivalent to repeatedly calling kelvin_metrics on each prefix.
    modes,coeff=transverse_mode_series(frames,frames[0],legacy_cfg['mode_min'],legacy_cfg['mode_max'])
    cps=[]
    for cp in cfg['checkpoints']:
        cp=int(cp)
        if cp>=len(frames):
            raise ValueError('checkpoint exceeds available frames')
        k=kelvin_metrics_from_series(modes,coeff[:cp+1],dt,legacy_cfg)
        cps.append({'checkpoint':cp,**k})
    late=[z for z in cps if z['checkpoint'] in set(map(int,cfg['late_checkpoints']))]
    counts={}
    for z in late:
        if z['pass'] and z['selected_mode'] is not None:
            counts[int(z['selected_mode'])]=counts.get(int(z['selected_mode']),0)+1
    winner=min(counts,key=lambda m:(-counts[m],m)) if counts else None
    q=[z for z in late if z['pass'] and z['selected_mode']==winner] if winner is not None else []
    f=np.asarray([z['frequency'] for z in q],float)
    cv=float(np.std(f)/max(abs(np.mean(f)),1e-12)) if len(f)>=2 and np.all(np.isfinite(f)) else float('inf')
    final_ok=any(z['checkpoint']==int(cfg['late_checkpoints'][-1]) and z['pass'] and z['selected_mode']==winner for z in q)
    passed=bool(winner is not None and len(q)>=int(cfg['minimum_qualified_checkpoints']) and cv<=float(cfg['frequency_cv_max']) and (final_ok or not bool(cfg.get('require_final_checkpoint_qualified',False))))
    sel=[z['selected_mode'] for z in cps]
    switches=sum(1 for a,b in zip(sel[:-1],sel[1:]) if a!=b)
    return {'status':'PERSISTENT_TRANSVERSE_MODE' if passed else 'MODAL_PERSISTENCE_NOT_REPRODUCED','pass':passed,'persistent_mode':winner,'qualified_late_checkpoints':len(q),'frequency_cv':cv,'final_checkpoint_qualified':bool(final_ok),'mode_switch_count':int(switches),'checkpoints':cps}

def aggregate_groups(carriers, cfg):
    groups={}
    for c in carriers:
        groups.setdefault(c['group_id'],[]).append(c)
    out=[]
    for gid,rows in sorted(groups.items()):
        counts={}
        for r in rows:
            p=r['persistence']
            if p['pass'] and p['persistent_mode'] is not None:
                counts[int(p['persistent_mode'])]=counts.get(int(p['persistent_mode']),0)+1
        mode=min(counts,key=lambda m:(-counts[m],m)) if counts else None
        supporting=[r for r in rows if r['persistence']['pass'] and r['persistence']['persistent_mode']==mode] if mode is not None else []
        passed=bool(len(supporting)>=int(cfg['minimum_replicates_per_group']))
        out.append({'group_id':gid,'status':'MODAL_PERSISTENCE_GROUP_CONFIRMED' if passed else 'MODAL_PERSISTENCE_GROUP_NOT_CONFIRMED','pass':passed,'branch_mode':mode,'supporting_replicates':len(supporting),'replicate_count':len(rows),'supporting_carrier_ids':[r['carrier_id'] for r in supporting]})
    return out


def numerical_convergence(points, base_mode, core, reparam, chunk, cfg, legacy_cfg):
    cp=int(cfg['reference_checkpoint']); dt0=float(cfg['time_step_ladder'][0])
    resrows=[]
    for n in cfg['curve_resolution_ladder']:
        q=resample_closed(points,int(n)); fr=evolve_curve(q,core,dt0,cp,reparam,chunk); k=kelvin_metrics(fr,dt0,legacy_cfg)
        resrows.append({'curve_points':int(n),'dt':dt0,'steps':cp,**k})
    dtrows=[]; T=cp*dt0
    base_n=int(cfg['curve_resolution_ladder'][0]); q=resample_closed(points,base_n)
    for dt in cfg['time_step_ladder']:
        steps=int(round(T/float(dt))); fr=evolve_curve(q,core,float(dt),steps,reparam,chunk); k=kelvin_metrics(fr,float(dt),legacy_cfg)
        dtrows.append({'curve_points':base_n,'dt':float(dt),'steps':steps,**k})
    def assess(rows):
        same=all(r['pass'] and r['selected_mode']==base_mode for r in rows)
        f=np.asarray([r['frequency'] for r in rows],float)
        span=float((np.max(f)-np.min(f))/max(abs(np.mean(f)),1e-12)) if len(f)>1 and np.all(np.isfinite(f)) else float('inf')
        return same,span
    rs,rspan=assess(resrows); ds,dspan=assess(dtrows)
    passed=bool(rs and ds and rspan<=float(cfg['frequency_relative_span_max']) and dspan<=float(cfg['frequency_relative_span_max']))
    return {'status':'MODAL_NUMERICAL_CONVERGENCE_PASS' if passed else 'MODAL_NUMERICAL_CONVERGENCE_FAIL','pass':passed,'base_mode':base_mode,'resolution_frequency_relative_span':rspan,'timestep_frequency_relative_span':dspan,'resolution_rows':resrows,'timestep_rows':dtrows}
