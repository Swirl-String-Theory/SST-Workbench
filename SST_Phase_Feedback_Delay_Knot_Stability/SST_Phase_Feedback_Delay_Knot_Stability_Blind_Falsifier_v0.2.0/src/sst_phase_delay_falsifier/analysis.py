from __future__ import annotations
from pathlib import Path
import json,math,hashlib
import numpy as np
from scipy.stats import spearmanr
from .geometry import length,kabsch_rms
from .backend import min_gap,evolve_pair,BACKEND
from .modal import spectrum,physical_eigen_perturbation
from .packet import packet_group_velocity

def load_cfg(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def _json_safe(obj):
    if isinstance(obj,dict): return {str(k):_json_safe(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)): return [_json_safe(v) for v in obj]
    if isinstance(obj,np.ndarray): return [_json_safe(v) for v in obj.tolist()]
    if isinstance(obj,np.generic): obj=obj.item()
    if isinstance(obj,float) and not math.isfinite(obj): return None
    return obj

def dump(path,obj): Path(path).write_text(json.dumps(_json_safe(obj),indent=2,allow_nan=False),encoding='utf-8')
def candidate_scale(x,cfg):
    d=min_gap(x,cfg['geometry']['gap_exclusion'])
    if not np.isfinite(d) or d<=0: raise ValueError('invalid nonadjacent gap')
    return d

def _spectrum_cache(x,cfg):
    g=cfg['physics']['gamma_dimensionless']; d=candidate_scale(x,cfg); core=cfg['physics']['core_to_gap']*d
    eps=cfg['modal']['fd_eps_to_gap']*d; modes=list(range(cfg['modal']['m_min'],cfg['modal']['m_max']+1))
    rows,cache=spectrum(x,modes,g,core,eps)
    return d,core,rows,cache

def predict_one(x,cfg):
    g=cfg['physics']['gamma_dimensionless']; d,core,rows,cache=_spectrum_cache(x,cfg); L=length(x)
    tchar=L*L/max(abs(g),1e-300); bym={r['m']:r for r in rows}; packets=[]
    for m in cfg['packet']['modes']:
        if m not in bym: continue
        q=packet_group_velocity(x,int(m),g,core,d,tchar,cfg['packet'])
        r=bym[m]; tau=q['tau_loop'] if q['valid'] else np.nan
        theta=(r['omega']*tau)%(2*np.pi) if q['valid'] and r['omega']>cfg['modal']['omega_floor'] else np.nan
        D=1-np.cos(theta) if np.isfinite(theta) else np.nan
        q.update({'omega':r['omega'],'linear_sigma0':r['sigma'],'theta':float(theta) if np.isfinite(theta) else np.nan,
                  'delay_score':float(D) if np.isfinite(D) else np.nan,'dispersion_v_group_diagnostic':r.get('v_group',np.nan)})
        packets.append(q)
    valid=[q for q in packets if q['valid'] and np.isfinite(q['delay_score'])]
    D=float(np.median([q['delay_score'] for q in valid])) if valid else np.nan
    return {'backend':BACKEND,'length':L,'gap':d,'core':core,'tchar':tchar,
            'delay_score':D,'packet_valid_modes':len(valid),'packet_total_modes':len(packets),
            'packet_valid_fraction':len(valid)/len(packets) if packets else 0.0,
            'median_packet_r2':float(np.median([q['r2'] for q in valid])) if valid else np.nan,
            'packet_modes':packets,'modal_spectrum':rows}

def predict_all(blind_dir,cfg,out_path):
    out={'format':'SST-PFD-PREDICTIONS-2.0','config':cfg,'backend':BACKEND,'candidates':[]}
    for p in sorted(Path(blind_dir).glob('B*.npy')):
        q=predict_one(np.load(p),cfg); q['blind_id']=p.stem; out['candidates'].append(q)
    dump(out_path,out); return out

def _growth(times,deps):
    t=np.asarray(times); y=np.asarray(deps); floor=max(y[0]*1e-4,1e-16); ly=np.log(np.maximum(y,floor))
    i0=max(1,int(0.2*len(t))); A=np.vstack([t[i0:],np.ones(len(t)-i0)]).T
    slope,_=np.linalg.lstsq(A,ly[i0:],rcond=None)[0]
    return float(slope)

def measure_one(x,cfg):
    g=cfg['physics']['gamma_dimensionless']; d,core,rows,cache=_spectrum_cache(x,cfg); L=length(x)
    tchar=L*L/max(abs(g),1e-300); steps=cfg['nonlinear']['steps']; dt=cfg['nonlinear']['total_time_to_tchar']*tchar/steps
    amp=cfg['nonlinear']['perturb_to_gap']*d; sample_every=max(1,steps//cfg['nonlinear']['samples']); bym={r['m']:r for r in rows}
    mode_runs=[]
    for m in cfg['nonlinear']['modes']:
        if m not in bym or m not in cache: continue
        eig,basis=cache[m]; p=physical_eigen_perturbation(eig,basis); xp=x+amp*p
        evo=evolve_pair(x,xp,steps,dt,g,core,sample_every)
        deps=np.array([kabsch_rms(a,b)/d for a,b in zip(evo['a'],evo['b'])])
        raw=_growth(np.asarray(evo['times']),deps); dimless=raw*tchar
        mode_runs.append({'m':int(m),'growth_raw':raw,'growth_dimensionless':dimless,
                          'final_departure':float(deps[-1]),'final_gap_base':float(evo['final_gap_a']),'final_gap_pert':float(evo['final_gap_b'])})
    Y=float(np.median([q['growth_dimensionless'] for q in mode_runs])) if mode_runs else np.nan
    return {'backend':BACKEND,'observed_growth_dimensionless':Y,
            'observed_growth_raw_median':float(np.median([q['growth_raw'] for q in mode_runs])) if mode_runs else np.nan,
            'mode_runs':mode_runs,'tchar':tchar,'dt':dt,'steps':steps}

def measure_all(blind_dir,cfg,out_path):
    out={'format':'SST-PFD-MEASUREMENTS-2.0','config':cfg,'backend':BACKEND,'candidates':[]}
    for p in sorted(Path(blind_dir).glob('B*.npy')):
        q=measure_one(np.load(p),cfg); q['blind_id']=p.stem; out['candidates'].append(q)
    dump(out_path,out); return out

def grouped_split(canonical_hashes,min_train=3,min_holdout=3):
    hs=list(canonical_hashes)
    tr=np.array([int(hashlib.sha256(('PFD-v0.2-split:'+h).encode()).hexdigest(),16)%2==0 for h in hs],dtype=bool)
    if tr.sum()<min_train or (~tr).sum()<min_holdout:
        order=np.argsort(np.array(hs,dtype=object)); tr[:]=False
        # deterministic near-half allocation by canonical hash order
        for rank,j in enumerate(order): tr[j]=(rank%2==0)
    return tr

def fit_negative_linear(D,Y):
    D=np.asarray(D,float); Y=np.asarray(Y,float)
    dc=D-D.mean(); den=float(np.dot(dc,dc))
    b=float(np.dot(dc,Y-Y.mean())/den) if den>0 else 0.0
    b=min(0.0,b); a=float(np.mean(Y-b*D))
    return a,b

def evaluate(pred_path,measure_path,manifest_path,audit_path,out_path):
    pred=json.loads(Path(pred_path).read_text()); meas=json.loads(Path(measure_path).read_text())
    man=json.loads(Path(manifest_path).read_text()); audit=json.loads(Path(audit_path).read_text())
    cfg=pred['config']; gates=cfg['gates']; packet_cfg=cfg['packet']
    mp={q['blind_id']:q for q in man['items']}; P={q['blind_id']:q for q in pred['candidates']}; M={q['blind_id']:q for q in meas['candidates']}
    # Hard pseudoreplication invariant: one canonical geometry per blind row.
    canon=[q['canonical_sha256'] for q in man['items']]
    pseudorep_ok=(len(canon)==len(set(canon)))
    ids=[]
    for i in sorted(set(P)&set(M)&set(mp)):
        vals=[P[i]['delay_score'],M[i]['observed_growth_dimensionless']]
        if all(v is not None and np.isfinite(v) for v in vals) and P[i]['packet_valid_modes']>=packet_cfg['min_valid_modes_per_candidate']:
            ids.append(i)
    D=np.array([P[i]['delay_score'] for i in ids]); Y=np.array([M[i]['observed_growth_dimensionless'] for i in ids])
    valid_fraction=len(ids)/len(man['items']) if man['items'] else 0.0
    quality_ok=(pseudorep_ok and len(ids)>=gates['min_candidates'] and valid_fraction>=packet_cfg['min_valid_candidate_fraction'])
    if len(ids)>=3:
        rho,pv=spearmanr(D,Y); rho=float(rho) if np.isfinite(rho) else None; pv=float(pv) if np.isfinite(pv) else None
    else: rho=pv=None
    primary=bool(quality_ok and rho is not None and pv is not None and rho<=gates['spearman_rho_max'] and pv<=gates['spearman_p_max'])
    train=np.zeros(len(ids),dtype=bool); a=b=rmse0=rmse1=improve=None
    holdout_evaluable=False
    if len(ids)>=gates['min_candidates']:
        hs=[mp[i]['canonical_sha256'] for i in ids]
        train=grouped_split(hs,gates['holdout_min_train'],gates['holdout_min_test'])
        if train.sum()>=gates['holdout_min_train'] and (~train).sum()>=gates['holdout_min_test']:
            holdout_evaluable=True
            base=float(np.mean(Y[train])); a,b=fit_negative_linear(D[train],Y[train])
            y0=np.full((~train).sum(),base); y1=a+b*D[~train]
            rmse0=float(np.sqrt(np.mean((Y[~train]-y0)**2))); rmse1=float(np.sqrt(np.mean((Y[~train]-y1)**2)))
            improve=float((rmse0-rmse1)/rmse0) if rmse0>0 else 0.0
    holdout=bool(quality_ok and holdout_evaluable and b is not None and b<0 and improve is not None and improve>=gates['holdout_rmse_improvement_min'])
    mode=audit['mode']; novelty_ok=(mode!='confirmatory' or audit['confirmatory_eligible'])
    if not novelty_ok:
        status='INCONCLUSIVE'; reason='insufficient_novel_unique_geometries'
    elif not quality_ok:
        status='INCONCLUSIVE'; reason='dataset_or_packet_quality_gate_failed'
    elif primary and holdout:
        status='PASS'; reason='both_v0.2_confirmatory_gates_passed'
    else:
        status='FAIL'; reason='one_or_more_v0.2_confirmatory_gates_failed'
    claim_status=('CONFIRMATORY_'+status if mode=='confirmatory' else 'RETROSPECTIVE_ONLY')
    rows=[]
    for j,i in enumerate(ids):
        rows.append({'blind_id':i,'canonical_sha256':mp[i]['canonical_sha256'],'delay_score':P[i]['delay_score'],
                     'packet_valid_modes':P[i]['packet_valid_modes'],'median_packet_r2':P[i]['median_packet_r2'],
                     'observed_growth_dimensionless':M[i]['observed_growth_dimensionless'],
                     'split':'train' if train[j] else 'holdout'})
    out={'format':'SST-PFD-BLIND-EVALUATION-2.0','analysis_role':cfg.get('analysis_role','UNSPECIFIED'),'status':status,'claim_status':claim_status,'status_reason':reason,
         'mode':mode,'n_blind_unique':len(man['items']),'n_valid':len(ids),'valid_fraction':valid_fraction,
         'dataset_gate':{'pseudoreplication_free':pseudorep_ok,'confirmatory_novelty_ok':novelty_ok,'audit':audit,'pass_for_analysis':quality_ok and novelty_ok},
         'primary_rank_gate':{'spearman_rho':rho,'p':pv,'threshold_rho_max':gates['spearman_rho_max'],'threshold_p_max':gates['spearman_p_max'],'pass':primary},
         'negative_slope_holdout_gate':{'intercept_a':a,'slope_b':b,'constraint':'b <= 0','rmse_constant_baseline':rmse0,'rmse_delay':rmse1,
                                        'fractional_improvement':improve,'required_improvement':gates['holdout_rmse_improvement_min'],
                                        'train_n':int(train.sum()),'holdout_n':int((~train).sum()),'pass':holdout},
         'rows':rows}
    dump(out_path,out); return _json_safe(out)

def reveal(eval_path,key_path,out_path):
    e=json.loads(Path(eval_path).read_text()); k=json.loads(Path(key_path).read_text()); mp={q['blind_id']:q for q in k['items']}
    for r in e['rows']:
        q=mp[r['blind_id']]; r.update({'source_names':q['source_names'],'sources':q['sources'],'duplicate_count':q['duplicate_count']})
    dump(out_path,e); return e

def preparation_audit(key_path,out_path):
    k=json.loads(Path(key_path).read_text()); items=k['items']; mult=[q['duplicate_count'] for q in items]
    nsrc=sum(mult); nuniq=len(items); frac=nuniq/nsrc if nsrc else 0.0
    if frac<=0.50: cls='STRONG_ENDPOINT_COLLAPSE'
    elif frac>=0.80: cls='PREPARATION_SENSITIVE'
    else: cls='MIXED_ENDPOINT_SENSITIVITY'
    out={'format':'SST-PFD-PREPARATION-AUDIT-2.0','classification':cls,'n_source_files_selected':nsrc,'n_unique_geometries_selected':nuniq,
         'unique_fraction_selected':frac,'max_multiplicity':max(mult,default=0),
         'duplicate_groups':[{'canonical_sha256':q['canonical_sha256'],'duplicate_count':q['duplicate_count'],'source_names':q['source_names']} for q in items if q['duplicate_count']>1]}
    dump(out_path,out); return out
