from __future__ import annotations
from pathlib import Path
import json
import numpy as np
from .blind_geometry import load_components_npz,resample_closed_curve,rotate_components
from .physics import evaluate_static,evaluate_dynamic,backend_name,qualify_backend,fibonacci_sphere
from .seal import sha256_file

STATIC_CONV_METRICS=(
    'rel_eq_residual','farfield_anisotropy_r6','cross_stabilization',
    'separation_gradient_abs_max_norm','separation_curvature_median_norm',
)
DYNAMIC_CONV_METRICS=('shape_drift','linking_drift_max','centroid_separation_drift')


def _rotation():
    a=np.array([0.37,-0.61,0.70]); a=a/np.linalg.norm(a); th=0.731
    K=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3)+np.sin(th)*K+(1-np.cos(th))*(K@K)


def _load_config(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _dt_steps(cfg,n):
    T=float(cfg.get('dynamic_t_final',0.0))
    if T<=0: return None,0
    nref=float(cfg.get('dt_reference_resolution',min(cfg['resolutions'])))
    dtref=float(cfg.get('dt_reference',4e-5))
    dt_nom=dtref*(nref/float(n))**2
    steps=max(1,int(np.ceil(T/dt_nom)))
    return T/steps,steps


def run_blind(campaign:Path,config_path:Path):
    if '_private' in str(config_path).lower(): raise RuntimeError('blind code refuses private paths')
    manifest=json.loads((campaign/'BLIND_MANIFEST.json').read_text(encoding='utf-8')); cfg=_load_config(config_path)
    frozen_cfg=campaign/'BLIND_CONFIG.json'
    raw_cfg=Path(config_path).read_bytes()
    if frozen_cfg.exists() and frozen_cfg.read_bytes()!=raw_cfg: raise RuntimeError('campaign already contains a different frozen blind config')
    frozen_cfg.write_bytes(raw_cfg)
    bq=qualify_backend(cfg.get('backend_policy','prefer_native'),float(cfg.get('native_reference_abs_tol',1e-11)))
    (campaign/'BACKEND_QUALIFICATION.json').write_text(json.dumps(bq,indent=2),encoding='utf-8')
    if not bq['qualified']:
        raise RuntimeError(f"backend qualification failed: {bq}")
    backend=bq['backend']
    results=[]; R=_rotation(); far_dirs=fibonacci_sphere(int(cfg.get('farfield_directions',96)))
    maxN=max(cfg['resolutions']); temporal_factor=int(cfg.get('temporal_refine_factor',1))
    for row in manifest['candidates']:
        p=campaign/'blind_inputs'/row['file']
        if sha256_file(p)!=row['sha256']: raise RuntimeError('blind input hash mismatch')
        base=load_components_npz(p)
        for n in cfg['resolutions']:
            comps=[resample_closed_curve(c,n) for c in base]
            for core_ratio in cfg['core_ratios']:
                for sector in cfg.get('circulation_sectors',[f'Q{i}' for i in range(8)]):
                    s=evaluate_static(comps,core_ratio,sector,far_dirs=far_dirs,backend=backend,
                                      separation_epsilon=float(cfg.get('separation_epsilon',0.035)))
                    sr=evaluate_static(rotate_components(comps,R),core_ratio,sector,far_dirs=far_dirs@R.T,
                                       backend=backend,separation_epsilon=float(cfg.get('separation_epsilon',0.035)))
                    obj=max(abs(s[k]-sr[k]) for k in STATIC_CONV_METRICS)
                    rec={'anonymous_id':row['anonymous_id'],'N':n,'core_ratio':core_ratio,'sector':sector,**s,'objectivity_delta':obj}
                    dt,steps=_dt_steps(cfg,n)
                    if steps>0:
                        try:
                            dyn,_=evaluate_dynamic(comps,core_ratio,sector,dt,steps,backend=backend); rec.update(dyn)
                            if temporal_factor>1 and n==maxN:
                                dt2=dt/temporal_factor; steps2=steps*temporal_factor
                                dyn2,_=evaluate_dynamic(comps,core_ratio,sector,dt2,steps2,backend=backend)
                                for k in DYNAMIC_CONV_METRICS:
                                    rec[f'temporal_refinement_abs_{k}']=abs(float(dyn[k])-float(dyn2[k]))
                        except Exception as e:
                            rec.update({'shape_drift':None,'linking_drift_max':None,'centroid_separation_drift':None,
                                        'finite':False,'dynamic_error':type(e).__name__})
                    results.append(rec)
    rp=campaign/'BLIND_RESULTS.json'
    rp.write_text(json.dumps({'schema':'A054-BLIND-RESULTS-1.1','results':results},indent=2),encoding='utf-8')
    analysis=analyze(results,cfg,manifest,bq)
    ap=campaign/'ANALYSIS_BLIND.json'; ap.write_text(json.dumps(analysis,indent=2),encoding='utf-8')
    report=campaign/'REPORT_BLIND.md'; report.write_text(render_report(analysis,manifest),encoding='utf-8')
    seal={'schema':'A054-BLIND-SEAL-1.1','manifest_sha256':sha256_file(campaign/'BLIND_MANIFEST.json'),
          'results_sha256':sha256_file(rp),'analysis_sha256':sha256_file(ap),'report_sha256':sha256_file(report),
          'backend_qualification_sha256':sha256_file(campaign/'BACKEND_QUALIFICATION.json'),
          'config_sha256':sha256_file(frozen_cfg),'private_mapping_commitment':manifest['private_mapping_sha256']}
    (campaign/'BLIND_SEAL.json').write_text(json.dumps(seal,indent=2),encoding='utf-8')
    return analysis


def _conv_delta(a,b,k,cfg):
    if a.get(k) is None or b.get(k) is None: return False,np.inf,np.inf
    av=float(a[k]); bv=float(b[k]); ad=abs(av-bv); rd=ad/max(abs(bv),1e-12)
    abs_cfg=cfg.get('convergence_abs_tol',{})
    atol=float(abs_cfg.get(k,abs_cfg.get('default',0.0)))
    ok=(ad<=atol) or (rd<=float(cfg['convergence_rel_tol']))
    return ok,ad,rd


def _median_by_sector(fine,metric):
    out={}
    for sec in sorted(set(r['sector'] for r in fine)):
        vals=[r.get(metric) for r in fine if r['sector']==sec and r.get(metric) is not None]
        out[sec]=None if not vals else float(np.median(vals))
    return out


def _sector_statuses(fine,cfg):
    out={}
    for sec in sorted(set(r['sector'] for r in fine)):
        rows=[r for r in fine if r['sector']==sec]
        reasons=[]
        if any(not r.get('finite',True) for r in rows): reasons.append('nonfinite_dynamic')
        shapes=[r.get('shape_drift') for r in rows if r.get('shape_drift') is not None]
        links=[r.get('linking_drift_max') for r in rows if r.get('linking_drift_max') is not None]
        if shapes and max(shapes)>float(cfg['max_shape_drift']): reasons.append('shape_drift')
        if links and max(links)>float(cfg['max_linking_drift']): reasons.append('linking_drift')
        out[sec]={'status':'QUALIFIED_SHORT_HORIZON' if not reasons else 'FAIL_SHORT_HORIZON', 'reasons':reasons,
                  'median_shape_drift':None if not shapes else float(np.median(shapes)),
                  'median_linking_drift':None if not links else float(np.median(links))}
    return out


def _polarity_group(fine,allsec,opposed,sector_status):
    cross=_median_by_sector(fine,'cross_stabilization'); rel=_median_by_sector(fine,'rel_eq_residual')
    base=cross.get(allsec); base_rel=rel.get(allsec)
    opp=[cross.get(s) for s in opposed]; opp_rel=[rel.get(s) for s in opposed]
    if base is None or base_rel is None or any(x is None for x in opp+opp_rel):
        return {'evaluable':False,'selection_gate':False}
    deltas=[float(x-base) for x in opp]
    improvements=[float(base_rel-x) for x in opp_rel]
    sign_count=sum(1 for s,x in zip(opposed,opp) if base<=0 and x>0 and sector_status.get(s,{}).get('status')=='QUALIFIED_SHORT_HORIZON')
    gate=bool(base<=0 and sign_count>=2 and np.median(improvements)>0)
    return {
        'evaluable':True,'all_same_sector':allsec,'one_opposed_sectors':opposed,
        'all_same_cross_stabilization':float(base),'one_opposed_cross_stabilization':[float(x) for x in opp],
        'delta_cross_by_slot':deltas,'delta_cross_median':float(np.median(deltas)),
        'rel_eq_improvement_by_slot':improvements,'rel_eq_improvement_median':float(np.median(improvements)),
        'qualified_sign_reversal_count':int(sign_count),'selection_gate':gate,
    }


def analyze(results,cfg,manifest,backend_qualification=None):
    per={}
    for r in results: per.setdefault(r['anonymous_id'],[]).append(r)
    summaries={}
    for aid,rows in per.items():
        converged=True; reasons=[]
        by={(r['N'],r['core_ratio'],r['sector']):r for r in rows}
        Ns=sorted(set(r['N'] for r in rows))
        if len(Ns)>=2:
            for cr in sorted(set(r['core_ratio'] for r in rows)):
                for sec in cfg.get('circulation_sectors',[f'Q{i}' for i in range(8)]):
                    a=by.get((Ns[-2],cr,sec)); b=by.get((Ns[-1],cr,sec))
                    if a and b:
                        for k in STATIC_CONV_METRICS+DYNAMIC_CONV_METRICS:
                            if k in a or k in b:
                                ok,ad,rd=_conv_delta(a,b,k,cfg)
                                if not ok:
                                    converged=False; reasons.append(f'spatial:{k}:abs={ad:.3g}:rel={rd:.3g}:sec={sec}:core={cr:g}')
        obj=max((r['objectivity_delta'] for r in rows),default=np.inf)
        if obj>cfg['objectivity_abs_tol']:
            converged=False; reasons.append(f'objectivity:{obj:.3g}')
        if not all(r.get('finite',True) for r in rows):
            converged=False; reasons.append('nonfinite_dynamic')
        temporal_tol=cfg.get('temporal_convergence_abs_tol',{})
        for r in rows:
            for k in DYNAMIC_CONV_METRICS:
                key=f'temporal_refinement_abs_{k}'
                if key in r:
                    tol=float(temporal_tol.get(k,temporal_tol.get('default',np.inf)))
                    if r[key]>tol:
                        converged=False; reasons.append(f'temporal:{k}:{r[key]:.3g}>{tol:.3g}:sec={r["sector"]}')
        fine=[r for r in rows if r['N']==max(Ns)]
        secstat=_sector_statuses(fine,cfg)
        polarity={
            'per_component_quantum':_polarity_group(fine,'Q0',['Q1','Q2','Q3'],secstat),
            'fixed_total_equal_split':_polarity_group(fine,'Q4',['Q5','Q6','Q7'],secstat),
        }
        polarity['both_normalizations_gate']=bool(polarity['per_component_quantum'].get('selection_gate') and
                                                   polarity['fixed_total_equal_split'].get('selection_gate'))
        sector_medians={}
        for metric in ('rel_eq_residual','cross_stabilization','farfield_anisotropy_r6','shape_drift',
                       'linking_drift_max','centroid_separation_drift','separation_curvature_median_norm',
                       'separation_gradient_abs_max_norm'):
            sector_medians[metric]=_median_by_sector(fine,metric)
        summaries[aid]={
            'status':'NUMERICALLY_QUALIFIED' if converged else 'INCONCLUSIVE_NUMERICAL',
            'reasons':reasons,'n_records':len(rows),'sector_status':secstat,'polarity':polarity,
            'sector_medians':sector_medians,
            'median_rel_eq':float(np.median([r['rel_eq_residual'] for r in fine])),
            'median_cross_stabilization':float(np.median([r['cross_stabilization'] for r in fine])),
            'median_farfield_anisotropy_r6':float(np.median([r['farfield_anisotropy_r6'] for r in fine])),
            'median_shape_drift':None if not any(r.get('shape_drift') is not None for r in fine) else float(np.median([r['shape_drift'] for r in fine if r.get('shape_drift') is not None])),
            'median_separation_curvature':float(np.median([r['separation_curvature_median_norm'] for r in fine])),
        }
    return {
        'schema':'A054-BLIND-ANALYSIS-1.1','scientific_ready':manifest['scientific_ready'],'summaries':summaries,
        'semantic_identity_read':False,'private_manifest_read':False,
        'policy':'numerical qualification + preregistered polarity gate + metric table; no weighted winner score',
        'backend':backend_name(),'backend_qualification':backend_qualification or {},
        'polarity_preregistration':'2+1 selection requires all-same cross-stabilization <=0, at least two qualified one-opposed sectors >0, and positive median relative-equilibrium improvement; required independently in both circulation normalizations.',
    }


def render_report(a,m):
    lines=['# A054 v0.1.1 — BLIND report','',
           'No semantic identity table was available to this stage.','',
           f"Scientific-ready full factorial tournament: **{a['scientific_ready']}**",
           f"Backend: **{a['backend']}**",'',
           '| anonymous | numerical status | polarity gate | rel-eq | cross-stab | sep curvature | shape drift |',
           '|---|---|---|---:|---:|---:|---:|']
    for k,v in sorted(a['summaries'].items()):
        pg=v['polarity']['both_normalizations_gate']
        lines.append(f"| `{k}` | {v['status']} | {pg} | {v['median_rel_eq']:.6g} | {v['median_cross_stabilization']:.6g} | {v['median_separation_curvature']:.6g} | {v['median_shape_drift'] if v['median_shape_drift'] is not None else 'n/a'} |")
    lines += ['', '`INCONCLUSIVE_NUMERICAL` is not a physical FAIL. `NUMERICALLY_QUALIFIED` is not a particle assignment.',
              'Reveal must not recompute blind observables.']
    return '\n'.join(lines)+'\n'
