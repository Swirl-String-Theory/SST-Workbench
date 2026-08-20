from __future__ import annotations
from pathlib import Path
import csv,json,math,statistics
import numpy as np
from .seal import verify

def binom_one_sided_ge(k,n):
    if n<=0:return 1.0
    return float(sum(math.comb(n,j) for j in range(k,n+1))/(2**n))

def _read_json(p):return json.loads(Path(p).read_text(encoding='utf-8'))

def reveal(project_root,blind_dir,catalog_dir,config_path,private_dir,outdir):
    verify(project_root,blind_dir,catalog_dir,config_path,private_dir)
    blind=Path(blind_dir);priv=Path(private_dir);out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    cand={r['candidate_id']:r for r in csv.DictReader(open(priv/'candidate_key.csv',encoding='utf-8'))}
    pkey={r['pair_id']:r for r in csv.DictReader(open(priv/'pair_key.csv',encoding='utf-8'))}
    brows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));rows=[]
    for r in brows:
        key=pkey[r['pair_id']];comp=key['comparison'];top=key['topology'];winner=r['winner_anonymous'];ca=r['candidate_a'];cb=r['candidate_b']
        famA=cand[ca]['source_family'];famB=cand[cb]['source_family']
        if winner=='A':wf=famA
        elif winner=='B':wf=famB
        else:wf=winner.lower()
        med=float(r['median_log_ratio_A_over_B']) if r['median_log_ratio_A_over_B'] not in ('',None,'None') else float('nan')
        # Convert anonymous A/B log ratio into fseries/reference log ratio. Negative favors fseries.
        if famA=='fseries':effect=med
        elif famB=='fseries':effect=-med
        else:effect=float('nan')
        rows.append({**r,'comparison':comp,'topology':top,'source_a':famA,'source_b':famB,'variant_a':cand[ca].get('variant',''),'variant_b':cand[cb].get('variant',''),'source_sha256_a':cand[ca].get('source_sha256',''),'source_sha256_b':cand[cb].get('source_sha256',''),'winner_source':wf,'log_ratio_fseries_over_reference':effect})
    fields=list(rows[0].keys()) if rows else ['pair_id']
    with open(out/'revealed_pair_results.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    cfg=_read_json(config_path);alpha=float(cfg.get('reveal_alpha',0.05));min_eff=float(cfg.get('reveal_min_effect_fraction',0.10));roll=[]
    for comp in sorted(set(r['comparison'] for r in rows)):
        rr=[r for r in rows if r['comparison']==comp and r['winner_source'] not in ('tie','indeterminate')]
        fw=sum(r['winner_source']=='fseries' for r in rr);rw=sum(r['winner_source']!='fseries' for r in rr);n=fw+rw;p=binom_one_sided_ge(fw,n);effects=[float(r['log_ratio_fseries_over_reference']) for r in rr if np.isfinite(float(r['log_ratio_fseries_over_reference']))];med=float(statistics.median(effects)) if effects else float('nan')
        if n and p<=alpha and med<=-math.log(1+min_eff):verdict='SUPPORTS_FSERIES_DYNAMIC_ADVANTAGE'
        elif n and binom_one_sided_ge(rw,n)<=alpha and med>=math.log(1+min_eff):verdict='FALSIFIES_FSERIES_ADVANTAGE'
        else:verdict='INDETERMINATE'
        roll.append({'comparison':comp,'n_non_ties':n,'fseries_wins':fw,'reference_wins':rw,'one_sided_sign_p_fseries':p,'median_log_ratio_fseries_over_reference':med,'median_ratio_fseries_over_reference':float(math.exp(med)) if np.isfinite(med) else float('nan'),'verdict':verdict})
    # Separate torus summary is explicit because the hypothesis originated there.
    torus_ids={'3_1','5_1','7_1','8_19','9_1','10_124'}
    tor=[r for r in rows if r['topology'] in torus_ids and r['comparison']=='fseries_vs_ideal' and r['winner_source'] not in ('tie','indeterminate')]
    tfw=sum(r['winner_source']=='fseries' for r in tor);tn=len(tor);tp=binom_one_sided_ge(tfw,tn) if tn else 1.0
    te=[float(r['log_ratio_fseries_over_reference']) for r in tor if np.isfinite(float(r['log_ratio_fseries_over_reference']))];tmed=float(statistics.median(te)) if te else float('nan')
    tor_summary={'n_non_ties':tn,'fseries_wins':tfw,'ideal_wins':tn-tfw,'one_sided_sign_p_fseries':tp,'median_log_ratio_fseries_over_ideal':tmed,'median_ratio_fseries_over_ideal':float(math.exp(tmed)) if np.isfinite(tmed) else float('nan'),'note':'With only 3-4 torus pairs, even unanimous wins may not reach p<=0.05; report effect size and sign-test p without lowering the preregistered alpha.'}
    summary={'seal_verified':True,'aggregate':roll,'torus_stratum':tor_summary,'interpretation':'A ratio below 1 means the fseries candidate had the lower preregistered dynamical-departure score. Source labels were joined only after the blind tree and code were sealed.'}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    lines=['# Fourier vs Ideal — post-seal reveal','','Blind seal verification: **PASS**.','', '## Aggregate']
    for x in roll:lines += [f"- `{x['comparison']}`: {x['verdict']}; fseries wins {x['fseries_wins']}/{x['n_non_ties']}; one-sided sign p={x['one_sided_sign_p_fseries']:.6g}; median fseries/reference ratio={x['median_ratio_fseries_over_reference']:.6g}."]
    lines += ['', '## Torus stratum',f"Fseries wins {tfw}/{tn}; p={tp:.6g}; median ratio={tor_summary['median_ratio_fseries_over_ideal']:.6g}.",'', 'No thresholds or scores are changed during reveal.']
    (out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return summary
