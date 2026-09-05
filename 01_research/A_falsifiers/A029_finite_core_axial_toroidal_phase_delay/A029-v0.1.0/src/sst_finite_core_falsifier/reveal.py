from __future__ import annotations
from pathlib import Path
import csv,json,math,shutil
import numpy as np
from .seal import verify
from .delay import circular_regression_cv

def _binom_tail(k,n):return sum(math.comb(n,j) for j in range(k,n+1))/(2**n) if n else 1.0

def reveal(root,blind,catalog,config,private,outdir):
    verify(root,blind,catalog,config);blind=Path(blind);catalog=Path(catalog);private=Path(private);out=Path(outdir)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True);cfg=json.loads(Path(config).read_text(encoding='utf-8'));keys={x['pair_id']:x for x in json.loads((private/'pair_key.json').read_text(encoding='utf-8'))};rows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));case_dir=blind/'cases';revealed=[];phase_rows=[]
    for row in rows:
        k=keys[row['pair_id']]; mapping={k['candidate_a']:k['condition_a'],k['candidate_b']:k['condition_b']}; win=row.get('winner_anonymous'); win_cand=k['candidate_a'] if win=='A' else k['candidate_b'] if win=='B' else None; wincond=mapping.get(win_cand,win)
        ca=json.loads((case_dir/f"{k['candidate_a']}.json").read_text(encoding='utf-8'));cb=json.loads((case_dir/f"{k['candidate_b']}.json").read_text(encoding='utf-8')); bycond={k['condition_a']:ca,k['condition_b']:cb};closed=bycond['CLOSED'];ctrl=bycond['OFFSET_CONTROL'];gc=float(closed.get('growth_metric',np.nan));go=float(ctrl.get('growth_metric',np.nan));ratio=gc/max(go,1e-12) if np.isfinite(gc) and np.isfinite(go) else np.nan
        revealed.append({**k,'winner_condition':wincond,'closed_growth':gc,'control_growth':go,'closed_over_control_growth':ratio,'closed_loop_phase':closed.get('loop_phase'),'closed_tau_error':closed.get('tau_relative_error'),'closed_hybridization':closed.get('hybridization_metric'),'closed_mode_valid':closed.get('eigenmode_gate_valid'),'control_mode_valid':ctrl.get('eigenmode_gate_valid')})
        if closed.get('eigenmode_gate_valid') and ctrl.get('eigenmode_gate_valid') and np.isfinite(closed.get('loop_phase',np.nan)) and np.isfinite(gc) and np.isfinite(go):phase_rows.append((k['carrier_id'],float(closed['loop_phase']),float(np.log((gc+1e-6)/(go+1e-6)))))
    fields=list(revealed[0].keys()) if revealed else []
    with open(out/'revealed_pairs.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(revealed)
    # one independent vote per carrier: median log growth ratio across nuisance scans
    carrier_votes=[]
    for cid in sorted(set(x['carrier_id'] for x in revealed)):
        x=[r for r in revealed if r['carrier_id']==cid and np.isfinite(r['closed_over_control_growth']) and r['closed_over_control_growth']>0]; med=float(np.median([np.log(r['closed_over_control_growth']) for r in x])) if x else np.nan;carrier_votes.append({'carrier_id':cid,'median_log_closed_over_control_growth':med,'closed_better':bool(np.isfinite(med) and med<0)})
    ksum=sum(x['closed_better'] for x in carrier_votes);p=_binom_tail(ksum,len(carrier_votes)); effect=float(np.exp(np.nanmedian([x['median_log_closed_over_control_growth'] for x in carrier_votes]))) if carrier_votes else np.nan
    # phase predictive gate; phase optimum is discovered, never supplied
    if phase_rows:
        groups=np.array([x[0] for x in phase_rows]);phi=np.array([x[1] for x in phase_rows]);y=np.array([x[2] for x in phase_rows]);cv=circular_regression_cv(phi,y,groups)
        rng=np.random.default_rng(int(cfg.get('permutation_seed',8675309)));null=[]
        for _ in range(int(cfg.get('phase_permutations',499))):
            pp=phi.copy()
            for gg in np.unique(groups):
                ii=np.where(groups==gg)[0]; vv=pp[ii].copy(); rng.shuffle(vv); pp[ii]=vv
            null.append(circular_regression_cv(pp,y,groups)['cv_r2'])
        pperm=(1+sum(np.isfinite(z) and z>=cv['cv_r2'] for z in null))/(1+len(null)) if np.isfinite(cv['cv_r2']) else 1.0
    else:cv={'cv_r2':np.nan,'rmse':np.nan,'n':0};pperm=1.0
    taus=np.array([float(x['closed_tau_error']) for x in revealed if x.get('closed_tau_error') not in (None,'') and np.isfinite(float(x['closed_tau_error']))]);delay_med=float(np.median(taus)) if len(taus) else np.nan
    mode_fraction=float(np.mean([bool(x['closed_mode_valid']) for x in revealed])) if revealed else 0.;closure_pass=bool(p<=float(cfg.get('closure_sign_alpha',.05)) and effect<=float(cfg.get('closure_effect_ratio_max',.90)));phase_pass=bool(np.isfinite(cv['cv_r2']) and cv['cv_r2']>=float(cfg.get('phase_cv_r2_min',.15)) and pperm<=float(cfg.get('phase_perm_alpha',.05)));delay_pass=bool(np.isfinite(delay_med) and delay_med<=float(cfg.get('delay_relative_error_max',.25)));mode_pass=bool(mode_fraction>=float(cfg.get('mode_valid_fraction_min',.70)))
    verdict='SUPPORTS_SELF_GENERATED_PHASE_FEEDBACK_MECHANISM' if all((closure_pass,phase_pass,delay_pass,mode_pass)) else 'MECHANISM_NOT_ESTABLISHED'
    summary={'format':'SST-FINITE-CORE-REVEAL-1','n_pairs':len(revealed),'n_carriers':len(carrier_votes),'carrier_closed_better':ksum,'carrier_sign_p_one_sided':p,'median_closed_over_control_growth_ratio':effect,'closure_advantage_gate':closure_pass,'finite_core_mode_valid_fraction':mode_fraction,'finite_core_mode_gate':mode_pass,'median_group_vs_wavepacket_delay_relative_error':delay_med,'self_generated_delay_gate':delay_pass,'phase_effect_cv_r2':cv['cv_r2'],'phase_effect_permutation_p':pperm,'phase_predictive_gate':phase_pass,'explicit_delay_parameter_used':False,'target_phase_used':False,'verdict':verdict,'carrier_votes':carrier_votes}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8');lines=['# Conclusions','',f'**Verdict:** `{verdict}`','',f'- finite-core mode valid fraction: {mode_fraction:.3f}',f'- median measured-delay error: {delay_med:.4g}',f'- carrier-level closed-loop sign p: {p:.4g}',f'- median closed/control growth ratio: {effect:.4g}',f'- phase-effect leave-one-carrier-out CV R²: {cv["cv_r2"]:.4g}',f'- grouped phase permutation p: {pperm:.4g}','','No delay or preferred phase is supplied to the dynamics. The loop delay is measured from finite-core dispersion and wave-packet return.'];(out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return summary
