from __future__ import annotations
import csv, json, math
from pathlib import Path
import numpy as np


def _finite(x):
    try: return math.isfinite(float(x))
    except Exception: return False


def fit_power_tail(N, y, *, p_min=0.25, p_max=4.0, p_grid=751):
    """Diagnostic fit y(N)=y_inf+c*N**(-p).

    The fit is never sufficient by itself for a convergence conclusion; callers
    must additionally require measured-tail support.
    """
    N=np.asarray(N,float); y=np.asarray(y,float)
    best=None
    for p in np.linspace(float(p_min),float(p_max),int(p_grid)):
        x=N**(-p); A=np.column_stack([np.ones_like(x),x])
        coef, *_=np.linalg.lstsq(A,y,rcond=None)
        pred=A@coef; rms=float(np.sqrt(np.mean((pred-y)**2)))
        rec=(rms,float(coef[0]),float(coef[1]),float(p))
        if best is None or rec[0]<best[0]: best=rec
    rms,yinf,c,p=best
    return {'y_inf':yinf,'c':c,'p':p,'rms':rms}


def tail3(y, *, threshold_scale, contraction_ratio_max, relative_tail_max):
    a,b,c=map(float,y); d1=b-a; d2=c-b
    tiny=1e-14*max(1.0,abs(a),abs(b),abs(c))
    if abs(d1)<=tiny and abs(d2)<=tiny:
        ratio=0.0; quasi=True; contracting=True
    elif abs(d1)<=tiny:
        ratio=float('inf'); quasi=False; contracting=False
    else:
        ratio=abs(d2)/abs(d1)
        quasi=(d1*d2>=-tiny*tiny)
        contracting=(ratio<=float(contraction_ratio_max))
    rel=abs(d2)/max(abs(c),float(threshold_scale),1e-30)
    return {
      'values':[a,b,c], 'delta_1':d1,'delta_2':d2,
      'quasi_monotone':bool(quasi),'contraction_ratio':float(ratio),
      'contracting':bool(contracting),'relative_last_step':float(rel),
      'relative_tail_ok':bool(rel<=float(relative_tail_max)),
      'converged':bool(quasi and contracting and rel<=float(relative_tail_max)),
    }


def _p2(r, threshold):
    g=float(r['metrics']['normalized_growth']); return bool(g<=threshold)


def analyze_ladder(rung_payloads, plan):
    """Analyze completed rung payloads keyed by rung name.

    Each payload: {'results': {blind_id: result}, 'mapping': {blind_id: meta}}
    Results are joined by unblinded source name so shard-local blind IDs do not
    leak into cross-shard semantics.
    """
    rungs=plan['rungs']; cmp=plan['comparison']; thr=float(cmp['growth_threshold'])
    by_source={}
    for rd in rungs:
        name=rd['name']; pay=rung_payloads[name]
        for bid,r in pay['results'].items():
            src=pay['mapping'][bid]['source']
            by_source.setdefault(src,{'source':src,'topology_class':pay['mapping'][bid].get('topology_class'),'canonical_id':pay['mapping'][bid].get('canonical_id'),'rungs':{}})
            by_source[src]['rungs'][name]=r
    records=[]
    for src,obj in sorted(by_source.items()):
        rr=obj['rungs']
        if any(rd['name'] not in rr for rd in rungs):
            obj['classification']='INCOMPLETE'; obj['missing_rungs']=[rd['name'] for rd in rungs if rd['name'] not in rr]; obj.pop('rungs',None); records.append(obj); continue
        g=[float(rr[rd['name']]['metrics']['normalized_growth']) for rd in rungs]
        # R0,R1,R2 isolate N at fixed k=8. R2,R3,R4 isolate k at fixed N=720.
        spatial=tail3(g[0:3],threshold_scale=thr,contraction_ratio_max=cmp['tail_contraction_ratio_max'],relative_tail_max=cmp['spatial_relative_tail_max'])
        spectral=tail3([g[2],g[3],g[4]],threshold_scale=thr,contraction_ratio_max=cmp['tail_contraction_ratio_max'],relative_tail_max=cmp['spectral_relative_tail_max'])
        p2_sp=[_p2(rr[rungs[i]['name']],thr) for i in (0,1,2)]
        p2_sk=[_p2(rr[rungs[i]['name']],thr) for i in (2,3,4)]
        spatial['verdict_stable']=len(set(p2_sp))==1
        spectral['verdict_stable']=len(set(p2_sk))==1
        r4=rr[rungs[4]['name']]; r5=rr[rungs[5]['name']]
        dmd=r4.get('dominant_mode_diagnostics',{})
        boundary=float(dmd.get('kmax_boundary_weight',r4['metrics'].get('dominant_kmax_boundary_weight',float('nan'))))
        basis_present=bool(dmd.get('kmax_basis_present',r4['metrics'].get('kmax_basis_present',False)))
        boundary_ok=basis_present and _finite(boundary) and boundary<=float(cmp['dominant_kmax_boundary_weight_max'])
        fit=fit_power_tail([rungs[i]['N'] for i in (0,1,2)],g[0:3],p_min=cmp['extrapolation_p_min'],p_max=cmp['extrapolation_p_max'],p_grid=cmp['extrapolation_p_grid'])
        fit['tail_supported']=bool(spatial['converged'] and spatial['verdict_stable'] and fit['p']>=cmp['extrapolation_p_min'])
        if fit['tail_supported']:
            unc=max(abs(spatial['delta_2']),abs(fit['y_inf']-g[2]))
            fit['uncertainty_proxy']=float(unc)
            fit['threshold_interval_crosses']=bool((fit['y_inf']-unc)<=thr<=(fit['y_inf']+unc))
        else:
            fit['uncertainty_proxy']=None; fit['threshold_interval_crosses']=None
        eps_drift=float(r5['metrics'].get('jacobian_robustness_relative_drift_max',0.0))
        eps_ok=eps_drift<=float(cmp['epsilon_robustness_J_drift_warn'])
        repeat_rel=abs(g[5]-g[4])/max(abs(g[4]),thr,1e-30)
        resolved=bool(spatial['converged'] and spatial['verdict_stable'] and spectral['converged'] and spectral['verdict_stable'] and boundary_ok)
        final_p2=bool(g[5]<=thr)
        if resolved and not (fit['tail_supported'] and fit.get('threshold_interval_crosses') is True):
            classification='CONVERGED_PASS' if final_p2 else 'CONVERGED_FAIL'
        else:
            classification='UNRESOLVED'
        reasons=[]
        if classification=='UNRESOLVED': reasons.append('resolution_or_threshold_unresolved')
        if abs(g[5]-thr)<=float(cmp['threshold_margin_for_fp64_confirmation']): reasons.append('near_growth_threshold')
        if classification=='CONVERGED_PASS': reasons.append('all_converged_passes_require_reference_audit')
        if not eps_ok: reasons.append('large_epsilon_J_drift')
        if not basis_present: reasons.append('kmax_basis_missing_after_orthonormalization')
        elif not boundary_ok: reasons.append('dominant_mode_hits_kmax_boundary')
        if bool(r5['metrics'].get('rpo_found')): reasons.append('rpo_candidate')
        if bool(r5['metrics'].get('floquet_valid')): reasons.append('floquet_candidate')
        obj.update({
          'growth_by_rung':{rungs[i]['name']:g[i] for i in range(len(rungs))},
          'status_by_rung':{rungs[i]['name']:rr[rungs[i]['name']]['status'] for i in range(len(rungs))},
          'p2_by_rung':{rungs[i]['name']:bool(g[i]<=thr) for i in range(len(rungs))},
          'spatial_tail':spatial,'spectral_tail':spectral,'spatial_extrapolation':fit,
          'kmax_boundary_weight':float(boundary) if _finite(boundary) else None,'kmax_basis_present':bool(basis_present),'kmax_boundary_ok':bool(boundary_ok),
          'epsilon_robustness_J_drift_max':eps_drift,'epsilon_robustness_warn_ok':bool(eps_ok),
          'R4_R5_repeatability_relative_growth_delta':float(repeat_rel),
          'classification':classification,'final_growth':g[5],
          'cpu_fp64_confirmation_required':bool(reasons),'cpu_fp64_reasons':reasons,
          'final_status':r5['status'], 'rpo_found':bool(r5['metrics'].get('rpo_found')), 'floquet_valid':bool(r5['metrics'].get('floquet_valid')),
        })
        obj.pop('rungs',None)
        records.append(obj)
    return records


def write_ladder_outputs(out_dir, records, plan):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    summary={'version':plan['version'],'plan':plan,'counts':{},'records':records}
    from collections import Counter
    summary['counts']=dict(Counter(r.get('classification','?') for r in records))
    (out/'LADDER_RESULTS.json').write_text(json.dumps(summary,indent=2,default=float)+'\n',encoding='utf-8')
    # Flat CSV
    rows=[]; rungs=plan['rungs']
    for r in records:
        row={'source':r['source'],'topology_class':r.get('topology_class'),'canonical_id':r.get('canonical_id'),'classification':r.get('classification')}
        for rd in rungs: row['g_'+rd['name']]=r.get('growth_by_rung',{}).get(rd['name'])
        row.update({
          'spatial_converged':r.get('spatial_tail',{}).get('converged'),
          'spatial_tail_ratio':r.get('spatial_tail',{}).get('contraction_ratio'),
          'spatial_last_relative_step':r.get('spatial_tail',{}).get('relative_last_step'),
          'spectral_converged':r.get('spectral_tail',{}).get('converged'),
          'spectral_tail_ratio':r.get('spectral_tail',{}).get('contraction_ratio'),
          'spectral_last_relative_step':r.get('spectral_tail',{}).get('relative_last_step'),
          'g_inf':r.get('spatial_extrapolation',{}).get('y_inf'),'fit_p':r.get('spatial_extrapolation',{}).get('p'),
          'fit_tail_supported':r.get('spatial_extrapolation',{}).get('tail_supported'),
          'kmax_boundary_weight':r.get('kmax_boundary_weight'),'kmax_basis_present':r.get('kmax_basis_present'),'epsilon_J_drift_max':r.get('epsilon_robustness_J_drift_max'),
          'R4_R5_repeatability_rel':r.get('R4_R5_repeatability_relative_growth_delta'),
          'cpu_fp64_confirmation_required':r.get('cpu_fp64_confirmation_required'),
          'cpu_fp64_reasons':';'.join(r.get('cpu_fp64_reasons',[])),
        }); rows.append(row)
    if rows:
        with (out/'LADDER_SUMMARY.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # Human report
    c=summary['counts']; lines=['# SST v0.4.7 High-Resolution DD32 Convergence Ladder','',
      f"Datasets analyzed: **{len(records)}**.",'',
      f"- CONVERGED_PASS: **{c.get('CONVERGED_PASS',0)}**",
      f"- CONVERGED_FAIL: **{c.get('CONVERGED_FAIL',0)}**",
      f"- UNRESOLVED: **{c.get('UNRESOLVED',0)}**",
      f"- INCOMPLETE: **{c.get('INCOMPLETE',0)}**",'',
      '## Decision discipline','',
      '- Spatial convergence uses R0/R1/R2: N=360/540/720 at fixed k_max=8.',
      '- Spectral convergence uses R2/R3/R4: k_max=8/12/16 at fixed N=720.',
      '- A power-tail extrapolation is diagnostic only and is accepted only when the measured tail is quasi-monotone, contracting, and verdict-stable.',
      '- R5 keeps the reference Jacobian at eps=0.004. eps=0.012/0.016 are separate finite-amplitude robustness probes and do not enter P1.',
      '- Large weight on the k_max=16 basis boundary marks spectral truncation unresolved.',
      '- DD32 is not IEEE FP64; the generated confirmation queue identifies cases requiring CPU/OpenMP FP64 audit.','',
      '## Most threshold-sensitive / unresolved','',
      '| source | class | final g | spatial | spectral | kmax weight | eps J drift | FP64 reasons |','|---|---|---:|---|---|---:|---:|---|']
    order=sorted(records,key=lambda r:(r.get('classification')!='UNRESOLVED',abs(float(r.get('final_growth',999))-plan['comparison']['growth_threshold']) if _finite(r.get('final_growth')) else 999))
    for r in order[:40]:
        lines.append(f"| {r['source']} | {r.get('classification')} | {r.get('final_growth',float('nan')):.7g} | {r.get('spatial_tail',{}).get('converged')} | {r.get('spectral_tail',{}).get('converged')} | {r.get('kmax_boundary_weight') if r.get('kmax_boundary_weight') is not None else float('nan'):.4g} | {r.get('epsilon_robustness_J_drift_max',float('nan')):.4g} | {', '.join(r.get('cpu_fp64_reasons',[]))} |")
    (out/'LADDER_CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    queue=[{'source':r['source'],'classification':r.get('classification'),'final_growth':r.get('final_growth'),'reasons':r.get('cpu_fp64_reasons',[])} for r in records if r.get('cpu_fp64_confirmation_required')]
    (out/'CPU_FP64_CONFIRMATION_QUEUE.json').write_text(json.dumps(queue,indent=2)+'\n',encoding='utf-8')
    (out/'CPU_FP64_CONFIRMATION_QUEUE.txt').write_text('\n'.join(q['source']+'\t'+','.join(q['reasons']) for q in queue)+'\n',encoding='utf-8')
    return summary
