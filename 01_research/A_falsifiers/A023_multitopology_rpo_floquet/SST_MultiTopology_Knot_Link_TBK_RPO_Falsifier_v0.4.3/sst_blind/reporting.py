from __future__ import annotations
from pathlib import Path
import csv, json
import numpy as np
from .gate_catalog import GATE_CATALOG


def _plain(x):
    if isinstance(x,(np.floating,np.integer)): return x.item()
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,dict): return {str(k):_plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_plain(v) for v in x]
    return x


def _fmt(v):
    if v is None: return 'n/a'
    if isinstance(v,bool): return str(v)
    if isinstance(v,(int,np.integer)): return str(int(v))
    if isinstance(v,(float,np.floating)):
        if not np.isfinite(v): return str(v)
        return f'{float(v):.6g}'
    if isinstance(v,dict): return '{' + ', '.join(f'{k}: {_fmt(x)}' for k,x in v.items()) + '}'
    if isinstance(v,list): return '['+', '.join(_fmt(x) for x in v[:6])+(' …' if len(v)>6 else '')+']'
    return str(v)


def _write_csv(path,rows):
    if not rows:return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)


def make_reports(out_dir, final, results, mapping):
    out=Path(out_dir); plots=out/'plots';plots.mkdir(exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except Exception:
        plt=None

    rows=[]; modal_rows=[]; contact_rows=[]; ablation_rows=[]; coupled_rows=[]; family_rows=[]; rpo_rows=[]; floquet_rows=[]; phase_rows=[]; gate_json={}
    for bid,r in results.items():
        sc=final['blind_scores'][bid]
        rows.append(dict(blind_id=bid,source=mapping[bid]['source'],status=sc['status'],**sc['metrics']))
        gate_json[bid]={'source':mapping[bid]['source'],'status':sc['status'],'gates':sc['gate_details']}
        for m in r.get('modal_attribution',[]):
            rr={'blind_id':bid,'source':mapping[bid]['source'],'rank':m['rank_by_real'],'eig_re':m['eigenvalue']['re'],'eig_im':m['eigenvalue']['im'],'dominant_sector':m['dominant_sector']}
            for k,z in m['contributions'].items(): rr[f'{k}_re']=z['re']; rr[f'{k}_im']=z['im']
            rr['m0']=m['sector_participation']['m0']; rr['E_tilt']=m['sector_participation']['E_tilt']; rr['E_breathe']=m['sector_participation']['E_breathe']; rr['reconstruction_abs_error']=m['reconstruction_abs_error']
            modal_rows.append(rr)
        for p in r['base'].get('contact_pair_diagnostics',{}).get('pairs',[]):
            rr={'blind_id':bid,'source':mapping[bid]['source'],'i':p['i'],'j':p['j'],'lobe_i':p['lobe_i'],'lobe_j':p['lobe_j'],'distance':p['distance'],'tangent_cos':p['tangent_cos'],'tangent_angle_deg':p['tangent_angle_deg']}
            for k,v in p['distance_rates'].items(): rr[f'{k}_rate']=v
            contact_rows.append(rr)
        for key,z in r.get('component_ablation',{}).items():
            ablation_rows.append({'blind_id':bid,'source':mapping[bid]['source'],'variant':key,'max_real':z['max_real'],'spectral_scale':z['spectral_scale'],'normalized_growth':z['normalized_growth']})
        cp=r.get('coupled_tbk') or {}
        for m in cp.get('spectrum',[]):
            rr={'blind_id':bid,'source':mapping[bid]['source'],'rank':m['rank'],'eig_re':m['eigenvalue']['re'],'eig_im':m['eigenvalue']['im']}
            for fam,val in m.get('family_participation',{}).items(): rr[f'{fam}_participation']=val
            coupled_rows.append(rr)
        for key,z in cp.get('family_coupling_ablation',{}).items():
            family_rows.append({'blind_id':bid,'source':mapping[bid]['source'],'variant':key,'max_real':z.get('max_real'),'spectral_scale':z.get('spectral_scale'),'normalized_growth':z.get('normalized_growth'),'growth_penalty_vs_full':z.get('growth_penalty_vs_full')})
        rpo=cp.get('rpo') or {}
        for q in rpo.get('scan',[]): rpo_rows.append({'blind_id':bid,'source':mapping[bid]['source'],'phase_index':q.get('phase_index'),'phase':q.get('phase'),'excursion_reached':q.get('excursion_reached'),'peak_before_return':q.get('peak_before_return'),'best_recurrence':q.get('best_recurrence'),'return_ratio':q.get('return_ratio'),'return_ratio_max':q.get('return_ratio_max'),'best_step':q.get('best_step'),'best_time':q.get('best_time'),'core_event':bool(q.get('core_event'))})
        fl=cp.get('floquet') or {}
        if fl.get('valid'):
            for i,z in enumerate(fl.get('multipliers',[])): floquet_rows.append({'blind_id':bid,'source':mapping[bid]['source'],'index':i,'re':z['re'],'im':z['im'],'abs':z['abs'],'neutral':i==fl.get('neutral_index')})
        pl=cp.get('phase_lock') or {}
        for q in pl.get('pairs',[]) if pl.get('valid') else []: phase_rows.append({'blind_id':bid,'source':mapping[bid]['source'],**q,'relative_frequency_spread':pl.get('relative_frequency_spread')})
    _write_csv(out/'summary_metrics.csv',rows); _write_csv(out/'modal_attribution.csv',modal_rows); _write_csv(out/'contact_pairs.csv',contact_rows); _write_csv(out/'component_ablation.csv',ablation_rows); _write_csv(out/'coupled_spectrum.csv',coupled_rows); _write_csv(out/'family_coupling_ablation.csv',family_rows); _write_csv(out/'rpo_phase_scan.csv',rpo_rows); _write_csv(out/'floquet_multipliers.csv',floquet_rows); _write_csv(out/'phase_lock.csv',phase_rows)
    (out/'gate_conclusions.json').write_text(json.dumps(_plain(gate_json),indent=2,sort_keys=True),encoding='utf-8')

    md=['# SST Trefoil Coupled Torsion–Breathing–Kelvin + RPO/Floquet Falsifier v0.3.0','',f"**Overall verdict:** `{final['overall']}`",'', '## Unblinded datasets']
    for bid in sorted(results):
        src=mapping[bid]['source'];sc=final['blind_scores'][bid];md += ['',f'### {bid} → {src}',f"Status: **{sc['status']}**",'', '| Gate | Role | Pass |','|---|---|---:|']
        for gid,val in sc['gates'].items(): md.append(f"| {gid} | {GATE_CATALOG[gid]['role']} | {val} |")
        dom=results[bid]['modal_attribution'][0]
        md += ['',f"Dominant reduced eigenvalue: `{dom['eigenvalue']['re']:.6g} {dom['eigenvalue']['im']:+.6g}i`",
               f"Dominant sector: `{dom['dominant_sector']}`; cross-lobe real contribution: `{dom['contributions']['cross_lobe']['re']:.6g}`."]
        cp=r.get('coupled_tbk') or {}; rp=(cp.get('rpo') or {}).get('candidate'); fl=cp.get('floquet') or {}; pl=cp.get('phase_lock') or {}
        if cp:
            md += [f"TBK expanded basis: `{len(cp.get('mode_names',[]))}` modes; RPO best recurrence: `{_fmt(rp.get('best_recurrence') if rp else None)}`; phase-lock strength: `{_fmt(pl.get('phase_lock_strength') if pl.get('valid') else None)}`; Floquet radius excl. neutral: `{_fmt(fl.get('spectral_radius_excluding_neutral') if fl.get('valid') else None)}`."]
    md += ['','## Circle null controls']
    for bid,z in sorted(final['circle_nulls'].items()): md += [f"- {bid}: radial mean `{z['radial_velocity_mean']:.6e}`, pass `{z['pass_null']}`"]
    md += ['', '## Interpretation',
           '`PASS` for the overall campaign still uses the immutable v0.1 critical set G0/G2/G3/G4/G6. v0.2 diagnostics G7–G11 remain unchanged; v0.3 adds G12–G19 for coupled torsion/breathing/Kelvin causality, phase locking, RPO recurrence and conditional Floquet stability without moving the original goalposts.',
           '', 'No reconnection, hard-core bounce, cut/splice, or penalty-force operator is present. Near-core events are reported only.',
           '', 'See `GATE_CONCLUSIONS.md` for every gate. v0.3 additionally writes `coupled_spectrum.csv`, `family_coupling_ablation.csv`, `phase_lock.csv`, `rpo_phase_scan.csv`, and `floquet_multipliers.csv`.']
    (out/'REPORT.md').write_text('\n'.join(md),encoding='utf-8')

    gd=['# Gate-by-gate conclusions','',f"Campaign verdict: **{final['overall']}**",'',
        'Each conclusion below is generated from the preregistered thresholds and the blind score. Critical versus diagnostic status is explicit so later versions can be compared without silently changing the v0.1 decision rule.']
    for bid in sorted(results):
        src=mapping[bid]['source']; sc=final['blind_scores'][bid]
        gd += ['',f'## {bid} → {src}',f"Dataset status: **{sc['status']}**"]
        for gid,det in sc['gate_details'].items():
            gd += ['',f"### {gid} — {det['title']}",f"**Role:** `{det['role']}`  ",f"**Verdict:** `{'PASS' if det['passed'] else 'FAIL'}`  ",
                   f"**Question:** {det['question']}", '', f"**Conclusion:** {det['conclusion']}", '', '**Evidence**']
            for k,v in det['measurements'].items(): gd.append(f'- `{k}` = `{_fmt(v)}`')
            gd += ['', '**Criterion**']
            for k,v in det['criterion'].items(): gd.append(f'- `{k}` = `{_fmt(v)}`')
        contacts=results[bid]['base']['contact_pair_diagnostics']; lobes=results[bid]['base']['lobe_pair_centroid_diagnostics']
        gd += ['', '### Orientation/contact synthesis',
               f"- Distinct close-contact cross-lobe separating fraction: `{contacts['positive_fraction']:.6g}`.",
               f"- Median cross-lobe separation rate across those contacts: `{contacts['median_cross_rate']:.6g}`.",
               f"- Correlation of separation rate with antiparallelness: `{_fmt(contacts['antiparallelness_rate_correlation'])}`.",
               f"- Lobe-centroid pair separating fraction: `{lobes['positive_fraction']:.6g}`."]
    (out/'GATE_CONCLUSIONS.md').write_text('\n'.join(gd),encoding='utf-8')

    if plt is None:return
    for bid,r in results.items():
        x=np.asarray(r['geometry']); fig=plt.figure(figsize=(7,6));ax=fig.add_subplot(111,projection='3d');lab=np.asarray(r['labels'])
        for k in range(3):
            q=x[lab==k];ax.plot(q[:,0],q[:,1],q[:,2],lw=1.2,label=f'lobe {k+1}')
        ax.set_title(f'{bid}: resampled blind geometry');ax.legend();fig.tight_layout();fig.savefig(plots/f'{bid}_geometry.png',dpi=180);plt.close(fig)
        j=r['jacobians'][len(r['jacobians'])//2]['eigs']; fig,ax=plt.subplots(figsize=(6,5))
        for key,mark in [('total','o'),('without_cross','x'),('cross_lobe','s')]:
            ev=j[key]['eigenvalues'];ax.scatter([z['re'] for z in ev],[z['im'] for z in ev],marker=mark,label=key)
        ax.axvline(0,lw=.8);ax.axhline(0,lw=.8);ax.set_xlabel('Re λ');ax.set_ylabel('Im λ');ax.set_title(f'{bid}: reduced Jacobian spectrum');ax.legend();fig.tight_layout();fig.savefig(plots/f'{bid}_eigenvalues.png',dpi=180);plt.close(fig)
        dom=r['modal_attribution'][0]; keys=['local','same_lobe','cross_lobe','transition']; vals=[dom['contributions'][k]['re'] for k in keys]
        fig,ax=plt.subplots(figsize=(7,4));ax.bar(keys,vals);ax.axhline(0,lw=.8);ax.set_ylabel('Re contribution to dominant λ');ax.set_title(f'{bid}: dominant-mode causal attribution');fig.tight_layout();fig.savefig(plots/f'{bid}_dominant_mode_attribution.png',dpi=180);plt.close(fig)
        cp=r['base']['contact_pair_diagnostics']['pairs']
        if cp:
            fig,ax=plt.subplots(figsize=(6,4));ax.scatter([p['tangent_cos'] for p in cp],[p['distance_rates']['cross_lobe'] for p in cp]);ax.axhline(0,lw=.8);ax.set_xlabel('t_i · t_j');ax.set_ylabel('cross-lobe distance rate');ax.set_title(f'{bid}: orientation vs separation');fig.tight_layout();fig.savefig(plots/f'{bid}_orientation_separation.png',dpi=180);plt.close(fig)
        rd=r.get('ringdown')
        if rd and rd.get('history'):
            h=rd['history'];fig,ax=plt.subplots(figsize=(7,4));ax.plot([z['t'] for z in h],[z['mode_amplitude'] for z in h]);ax.set_xlabel('dimensionless time');ax.set_ylabel(rd['mode']);ax.set_title(f'{bid}: nonlinear ringdown');fig.tight_layout();fig.savefig(plots/f'{bid}_ringdown.png',dpi=180);plt.close(fig)
        cf=r.get('counterfactual_ringdown')
        if cf:
            fig,ax=plt.subplots(figsize=(7,4))
            for key,z in cf['variants'].items():
                h=z['history'];ax.plot([q['t'] for q in h],[q['modal_norm'] for q in h],label=key)
            ax.set_xlabel('dimensionless time');ax.set_ylabel('six-mode norm');ax.set_title(f'{bid}: full vs no-cross counterfactual');ax.legend();fig.tight_layout();fig.savefig(plots/f'{bid}_counterfactual.png',dpi=180);plt.close(fig)
        cp=r.get('coupled_tbk') or {}
        if cp.get('spectrum'):
            sp=cp['spectrum']; fig,ax=plt.subplots(figsize=(6,5)); ax.scatter([z['eigenvalue']['re'] for z in sp],[z['eigenvalue']['im'] for z in sp]); ax.axvline(0,lw=.8); ax.axhline(0,lw=.8); ax.set_xlabel('Re λ'); ax.set_ylabel('Im λ'); ax.set_title(f'{bid}: expanded TBK/Kelvin spectrum'); fig.tight_layout(); fig.savefig(plots/f'{bid}_coupled_spectrum.png',dpi=180); plt.close(fig)
        rp=(cp.get('rpo') or {}).get('candidate')
        if rp and rp.get('history'):
            h=rp['history']; fig,ax=plt.subplots(figsize=(7,4)); ax.plot([q['t'] for q in h],[q['recurrence'] for q in h]); ax.axhline(float(cp.get('floquet',{}).get('threshold',0.0)) if False else 0.0,lw=.1); ax.set_xlabel('dimensionless time'); ax.set_ylabel('shape recurrence'); ax.set_title(f'{bid}: best RPO phase trajectory'); fig.tight_layout(); fig.savefig(plots/f'{bid}_rpo_recurrence.png',dpi=180); plt.close(fig)
        fl=cp.get('floquet') or {}
        if fl.get('valid'):
            mu=fl['multipliers']; fig,ax=plt.subplots(figsize=(5,5)); th=np.linspace(0,2*np.pi,256); ax.plot(np.cos(th),np.sin(th),lw=.8); ax.scatter([z['re'] for z in mu],[z['im'] for z in mu]); ax.set_aspect('equal',adjustable='box'); ax.set_xlabel('Re μ'); ax.set_ylabel('Im μ'); ax.set_title(f'{bid}: Floquet multipliers'); fig.tight_layout(); fig.savefig(plots/f'{bid}_floquet.png',dpi=180); plt.close(fig)
