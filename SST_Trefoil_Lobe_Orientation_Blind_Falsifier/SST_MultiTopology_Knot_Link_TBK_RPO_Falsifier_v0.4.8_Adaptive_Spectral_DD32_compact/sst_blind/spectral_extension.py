from __future__ import annotations
import csv, json, math, zipfile
from pathlib import Path
import numpy as np


def _finite(x):
    try:
        return math.isfinite(float(x))
    except Exception:
        return False


def fit_power_tail_k(k, y, *, p_min=0.25, p_max=6.0, p_grid=1151):
    """Diagnostic fit g(k_max)=g_inf+c*k_max**(-p).

    This fit is never sufficient for a convergence decision. Measured tail
    contraction, verdict stability, threshold separation and mode-tail closure
    are all required independently.
    """
    k=np.asarray(k,float); y=np.asarray(y,float)
    best=None
    for p in np.linspace(float(p_min),float(p_max),int(p_grid)):
        x=k**(-p)
        A=np.column_stack([np.ones_like(x),x])
        coef,*_=np.linalg.lstsq(A,y,rcond=None)
        pred=A@coef
        rms=float(np.sqrt(np.mean((pred-y)**2)))
        rec=(rms,float(coef[0]),float(coef[1]),float(p))
        if best is None or rec[0]<best[0]: best=rec
    rms,yinf,c,p=best
    return {'g_inf':yinf,'c':c,'p':p,'rms':rms}


def tail3(values, *, threshold_scale=0.12, contraction_ratio_max=0.75, relative_tail_max=0.03):
    a,b,c=map(float,values)
    d1=b-a; d2=c-b
    tiny=1e-14*max(1.0,abs(a),abs(b),abs(c))
    if abs(d1)<=tiny and abs(d2)<=tiny:
        ratio=0.0; quasi=True; contracting=True
    elif abs(d1)<=tiny:
        ratio=float('inf'); quasi=False; contracting=False
    else:
        ratio=abs(d2)/abs(d1)
        quasi=bool(d1*d2>=-tiny*tiny)
        contracting=bool(ratio<=float(contraction_ratio_max))
    rel=abs(d2)/max(abs(c),float(threshold_scale),1e-30)
    return {
      'values':[a,b,c], 'delta_1':float(d1),'delta_2':float(d2),
      'quasi_monotone':bool(quasi), 'contraction_ratio':float(ratio),
      'contracting':bool(contracting), 'relative_last_step':float(rel),
      'relative_tail_ok':bool(rel<=float(relative_tail_max)),
      'converged':bool(quasi and contracting and rel<=float(relative_tail_max)),
    }


def mode_tail_diagnostics(result, *, kmax, high_fraction=0.75, kelvin_total_min=0.05):
    d=result.get('dominant_mode_diagnostics',{}) or {}
    by={int(k):float(v) for k,v in (d.get('kelvin_k_weight',{}) or {}).items()}
    configured=d.get('configured_k_max')
    requested=d.get('requested_k_max',kmax)
    basis_present=bool(d.get('kmax_basis_present', configured==kmax)) and int(requested)==int(kmax)
    boundary=float(d.get('kmax_boundary_weight',by.get(int(kmax),float('nan'))))
    k_cut=int(math.ceil(float(high_fraction)*int(kmax)))
    kelvin_total=float(sum(by.values()))
    high_abs=float(sum(v for k,v in by.items() if k>=k_cut))
    high_within=(high_abs/kelvin_total) if kelvin_total>1e-30 else 0.0
    # If the dominant vector contains almost no Kelvin content at all, high-k
    # truncation cannot be the controlling mechanism; otherwise demand decay.
    tail_applicable=kelvin_total>=float(kelvin_total_min)
    return {
      'configured_k_max':configured,
      'requested_k_max':int(kmax),
      'kmax_basis_present':bool(basis_present),
      'kmax_boundary_weight':boundary if _finite(boundary) else None,
      'kelvin_total_weight':kelvin_total,
      'high_k_cutoff':k_cut,
      'high_k_absolute_weight':high_abs,
      'high_k_fraction_within_kelvin':high_within,
      'tail_gate_applicable':bool(tail_applicable),
      'kelvin_k_weight':{str(k):float(v) for k,v in sorted(by.items())},
    }


def evaluate_triplet(k_values, results, policy):
    """Evaluate one adaptive stop candidate using exactly three k_max rungs."""
    ks=list(map(int,k_values))
    gs=[float(r['metrics']['normalized_growth']) for r in results]
    thr=float(policy['growth_threshold'])
    t=tail3(gs,threshold_scale=thr,
            contraction_ratio_max=policy['tail_contraction_ratio_max'],
            relative_tail_max=policy['spectral_relative_tail_max'])
    verdicts=[g<=thr for g in gs]
    t['verdict_stable']=len(set(verdicts))==1
    last=results[-1]
    md=mode_tail_diagnostics(last,kmax=ks[-1],high_fraction=policy['high_k_fraction'],kelvin_total_min=policy['kelvin_total_weight_min_for_tail_gate'])
    boundary_ok=bool(md['kmax_basis_present'] and md['kmax_boundary_weight'] is not None and md['kmax_boundary_weight']<=float(policy['dominant_kmax_boundary_weight_max']))
    tail_energy_ok=bool((not md['tail_gate_applicable']) or md['high_k_fraction_within_kelvin']<=float(policy['high_k_fraction_within_kelvin_max']))
    nyquist_fraction=float(last.get('metrics',{}).get('spectral_nyquist_fraction',0.0))
    nyquist_safe=bool(last.get('metrics',{}).get('spectral_nyquist_safe',nyquist_fraction<=float(policy['spectral_nyquist_fraction_max']))) and nyquist_fraction<=float(policy['spectral_nyquist_fraction_max'])
    fit=fit_power_tail_k(ks,gs,p_min=policy['extrapolation_p_min'],p_max=policy['extrapolation_p_max'],p_grid=policy['extrapolation_p_grid'])
    fit_supported=bool(t['converged'] and t['verdict_stable'] and boundary_ok and tail_energy_ok and nyquist_safe)
    unc=max(abs(t['delta_2']),abs(fit['g_inf']-gs[-1])) if fit_supported else None
    threshold_crosses=bool((fit['g_inf']-unc)<=thr<=(fit['g_inf']+unc)) if unc is not None else None
    fit.update({'tail_supported':fit_supported,'uncertainty_proxy':unc,'threshold_interval_crosses':threshold_crosses})
    resolved=bool(t['converged'] and t['verdict_stable'] and boundary_ok and tail_energy_ok and nyquist_safe and not (threshold_crosses is True))
    reasons=[]
    if not t['quasi_monotone']: reasons.append('growth_tail_not_quasi_monotone')
    if not t['contracting']: reasons.append('growth_tail_not_contracting')
    if not t['relative_tail_ok']: reasons.append('growth_last_step_too_large')
    if not t['verdict_stable']: reasons.append('P2_verdict_changed_across_tail')
    if not md['kmax_basis_present']: reasons.append('kmax_basis_missing')
    if not boundary_ok: reasons.append('dominant_mode_hits_kmax_boundary')
    if not tail_energy_ok: reasons.append('high_k_mode_tail_not_decayed')
    if not nyquist_safe: reasons.append('spectral_nyquist_guard_failed')
    if threshold_crosses is True: reasons.append('extrapolation_uncertainty_crosses_threshold')
    return {
      'k_values':ks,'growth_values':gs,'growth_tail':t,'mode_tail':md,
      'boundary_ok':boundary_ok,'high_k_tail_ok':tail_energy_ok,'spectral_nyquist_fraction':nyquist_fraction,'spectral_nyquist_safe':nyquist_safe,
      'spectral_extrapolation':fit,'resolved':resolved,
      'growth_verdict':'PASS' if gs[-1]<=thr else 'FAIL','reasons':reasons,
    }


def _read_rung_folder(folder: Path):
    mf=folder/'unblind_manifest.json'; pre=folder/'pre_unblind'
    if not mf.exists() or not pre.exists():
        raise FileNotFoundError(f'not a completed rung folder: {folder}')
    mapping=json.loads(mf.read_text(encoding='utf-8'))
    out={}
    for bid,meta in mapping.items():
        af=pre/f'{bid}_analysis.json'
        if af.exists(): out[meta['source']]={'result':json.loads(af.read_text(encoding='utf-8')),'meta':meta}
    return out


def load_v047_k16_baseline(path):
    """Load R4 N720/K16 linear results from a v0.4.7 output dir or zip."""
    p=Path(path)
    if p.is_dir():
        # Accept the output root or the R4 folder itself.
        cand=p/'04_R4_N720_K16_SPECTRAL'
        return _read_rung_folder(cand if cand.exists() else p)
    if p.is_file() and p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
            mfs=[n for n in names if n.endswith('04_R4_N720_K16_SPECTRAL/unblind_manifest.json')]
            if not mfs: raise FileNotFoundError('v0.4.7 R4 K16 manifest not found in zip')
            mf=mfs[0]; prefix=mf[:-len('unblind_manifest.json')]
            mapping=json.loads(z.read(mf))
            out={}
            name_set=set(names)
            for bid,meta in mapping.items():
                af=prefix+f'pre_unblind/{bid}_analysis.json'
                if af in name_set:
                    out[meta['source']]={'result':json.loads(z.read(af)),'meta':meta}
            return out
    raise FileNotFoundError(path)


def load_rung_by_source(folder):
    return _read_rung_folder(Path(folder))


def write_extension_outputs(out_dir, records, plan):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    counts={}
    for r in records: counts[r['classification']]=counts.get(r['classification'],0)+1
    payload={'version':plan['version'],'plan':plan,'counts':counts,'records':records}
    (out/'SPECTRAL_EXTENSION_RESULTS.json').write_text(json.dumps(payload,indent=2,default=float)+'\n',encoding='utf-8')
    rows=[]
    for r in records:
        row={
          'source':r['source'],'topology_class':r.get('topology_class'),'canonical_id':r.get('canonical_id'),
          'classification':r['classification'],'growth_verdict':r.get('growth_verdict'),'final_kmax':r.get('final_kmax'),'final_growth':r.get('final_growth'),
          'tail_ratio':r.get('decision',{}).get('growth_tail',{}).get('contraction_ratio'),
          'last_relative_step':r.get('decision',{}).get('growth_tail',{}).get('relative_last_step'),
          'kmax_boundary_weight':r.get('decision',{}).get('mode_tail',{}).get('kmax_boundary_weight'),
          'high_k_fraction_within_kelvin':r.get('decision',{}).get('mode_tail',{}).get('high_k_fraction_within_kelvin'),
          'spectral_nyquist_fraction':r.get('decision',{}).get('spectral_nyquist_fraction'),
          'g_inf':r.get('decision',{}).get('spectral_extrapolation',{}).get('g_inf'),
          'fit_p':r.get('decision',{}).get('spectral_extrapolation',{}).get('p'),
          'threshold_crosses':r.get('decision',{}).get('spectral_extrapolation',{}).get('threshold_interval_crosses'),
          'reasons':';'.join(r.get('reasons',[])),
        }
        for k,g in sorted(r.get('growth_by_k',{}).items(),key=lambda kv:int(kv[0])): row[f'g_k{k}']=g
        rows.append(row)
    # stable columns: base + all k columns
    if rows:
        base=['source','topology_class','canonical_id','classification','growth_verdict','final_kmax','final_growth','tail_ratio','last_relative_step','kmax_boundary_weight','high_k_fraction_within_kelvin','spectral_nyquist_fraction','g_inf','fit_p','threshold_crosses','reasons']
        ks=sorted({int(c[3:]) for row in rows for c in row if c.startswith('g_k')})
        fields=base+[f'g_k{k}' for k in ks]
        with (out/'SPECTRAL_EXTENSION_SUMMARY.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
    lines=['# SST v0.4.8 Adaptive Spectral Convergence Extension','',f'Datasets: **{len(records)}**.','']
    for key in ('SPECTRAL_CONVERGED_K32','SPECTRAL_CONVERGED_K48','SPECTRAL_CONVERGED_K64','SPECTRAL_UNRESOLVED_AT_K64'):
        lines.append(f'- {key}: **{counts.get(key,0)}**')
    lines += ['', '## Preregistered decision rule','',
      '- Baseline: N=720, k_max=16 from v0.4.7 R4 or a recomputed S0.',
      '- Every dataset is evaluated at k_max=24 and 32.',
      '- Only unresolved datasets continue to k_max=48, then k_max=64.',
      '- A stop requires a quasi-monotone contracting 3-point growth tail, <=3% last relative step, stable P2 verdict, no threshold-overlap under the diagnostic power-tail uncertainty proxy, a present k_max basis, <=10% exact-boundary weight, a decayed high-k Kelvin tail, and k_max <= 0.75 of the least-sampled component Nyquist limit.',
      '- The fit g(k_max)=g_inf+c*k_max^{-p} is diagnostic only and cannot by itself create convergence.',
      '- SPECTRAL_UNRESOLVED_AT_K64 is a valid falsifier outcome; it is not coerced into PASS/FAIL.','',
      '## Results','',
      '| source | classification | P2 | k | g | tail ratio | last rel | boundary | high-k tail | reasons |','|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    order=sorted(records,key=lambda r:(r['classification']=='SPECTRAL_UNRESOLVED_AT_K64',r.get('final_growth',999)))
    for r in order:
        d=r.get('decision',{}); gt=d.get('growth_tail',{}); mt=d.get('mode_tail',{})
        lines.append(f"| {r['source']} | {r['classification']} | {r.get('growth_verdict')} | {r.get('final_kmax')} | {r.get('final_growth',float('nan')):.7g} | {gt.get('contraction_ratio',float('nan')):.4g} | {gt.get('relative_last_step',float('nan')):.4g} | {(mt.get('kmax_boundary_weight') if mt.get('kmax_boundary_weight') is not None else float('nan')):.4g} | {mt.get('high_k_fraction_within_kelvin',float('nan')):.4g} | {', '.join(r.get('reasons',[]))} |")
    (out/'SPECTRAL_EXTENSION_CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    unresolved=[r for r in records if r['classification']=='SPECTRAL_UNRESOLVED_AT_K64']
    (out/'SPECTRAL_UNRESOLVED_QUEUE.json').write_text(json.dumps(unresolved,indent=2,default=float)+'\n',encoding='utf-8')
    confirm=[{'source':r['source'],'classification':r['classification'],'growth_verdict':r.get('growth_verdict'),'final_kmax':r.get('final_kmax'),'final_growth':r.get('final_growth'),'reasons':(['spectrally_converged_growth_pass'] if r.get('growth_verdict')=='PASS' and r['classification'].startswith('SPECTRAL_CONVERGED') else []) + (['near_growth_threshold'] if abs(float(r.get('final_growth',999))-float(plan['policy']['growth_threshold']))<=float(plan['policy']['fp64_confirmation_margin']) else [])} for r in records if (r.get('growth_verdict')=='PASS' and r['classification'].startswith('SPECTRAL_CONVERGED')) or abs(float(r.get('final_growth',999))-float(plan['policy']['growth_threshold']))<=float(plan['policy']['fp64_confirmation_margin'])]
    (out/'CPU_FP64_CONFIRMATION_QUEUE.json').write_text(json.dumps(confirm,indent=2)+'\n',encoding='utf-8')
    return payload
