from __future__ import annotations
from pathlib import Path
import csv,json,math,shutil
import numpy as np
from .seal import verify
from .delay import circular_regression_cv,wrap


def _binom_tail(k,n):return sum(math.comb(n,j) for j in range(k,n+1))/(2**n) if n else 1.0

def _f(x,default=np.nan):
    try:return float(x)
    except Exception:return float(default)

def _target_phase_carrier_test(rows,target,m_target=1,min_rows=4):
    votes=[]
    for cid in sorted(set(r['carrier_id'] for r in rows)):
        rr=[r for r in rows if r['carrier_id']==cid and int(r['m'])==int(m_target) and r['both_valid'] and not r['neutral_pair'] and np.isfinite(r['closed_loop_phase']) and np.isfinite(r['log_growth_ratio'])]
        if len(rr)<int(min_rows):continue
        x=np.array([np.cos(wrap(r['closed_loop_phase']-target)) for r in rr],float); y=np.array([r['log_growth_ratio'] for r in rr],float)
        if np.ptp(x)<1e-5:continue
        X=np.c_[np.ones(len(x)),x]; q=np.linalg.lstsq(X,y,rcond=None)[0]; pred=X@q; den=float(np.sum((y-y.mean())**2)); r2=1-float(np.sum((y-pred)**2))/max(den,1e-30)
        slope=float(q[1]); votes.append({'carrier_id':cid,'n':len(rr),'target_phase_slope':slope,'r2':r2,'direction_correct':slope<0})
    k=sum(v['direction_correct'] for v in votes); n=len(votes); p=_binom_tail(k,n); med=float(np.median([v['target_phase_slope'] for v in votes])) if votes else np.nan
    return {'target_phase_rad':float(target),'m_target':int(m_target),'n_carriers':n,'direction_correct_carriers':k,'one_sided_sign_p':p,'median_carrier_slope':med,'carrier_votes':votes}


def reveal(root,blind,catalog,config,private,outdir):
    verify(root,blind,catalog,config);blind=Path(blind);catalog=Path(catalog);private=Path(private);out=Path(outdir)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True);cfg=json.loads(Path(config).read_text(encoding='utf-8'));keys={x['pair_id']:x for x in json.loads((private/'pair_key.json').read_text(encoding='utf-8'))};rows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));case_dir=blind/'cases';revealed=[];phase_rows=[];clock_rows=[]
    eps=float(cfg.get('neutral_growth_epsilon',1e-8))
    for row in rows:
        k=keys[row['pair_id']]; mapping={k['candidate_a']:k['condition_a'],k['candidate_b']:k['condition_b']}; win=row.get('winner_anonymous'); win_cand=k['candidate_a'] if win=='A' else k['candidate_b'] if win=='B' else None; wincond=mapping.get(win_cand,win)
        ca=json.loads((case_dir/f"{k['candidate_a']}.json").read_text(encoding='utf-8'));cb=json.loads((case_dir/f"{k['candidate_b']}.json").read_text(encoding='utf-8')); bycond={k['condition_a']:ca,k['condition_b']:cb};closed=bycond['CLOSED'];ctrl=bycond.get('SYMMETRIC_CONTROL',bycond.get('OFFSET_CONTROL'))
        gc=_f(closed.get('growth_metric'));go=_f(ctrl.get('growth_metric')); vc=bool(closed.get('eigenmode_gate_valid')); vo=bool(ctrl.get('eigenmode_gate_valid')); both=bool(vc and vo)
        neutral=bool(both and np.isfinite(gc) and np.isfinite(go) and max(gc,go)<=eps)
        logratio=float(np.log((gc+eps)/(go+eps))) if both and np.isfinite(gc) and np.isfinite(go) and not neutral else 0.0 if neutral else np.nan
        ratio=float(np.exp(logratio)) if np.isfinite(logratio) else np.nan
        sc=closed.get('swirl_clock',{}) if isinstance(closed.get('swirl_clock',{}),dict) else {}
        rec={**k,'winner_condition':wincond,'closed_growth':gc,'control_growth':go,'closed_over_control_growth':ratio,'log_growth_ratio':logratio,'neutral_pair':neutral,'both_valid':both,
             'closed_loop_phase':_f(closed.get('loop_phase')),'closed_tau_error':_f(closed.get('tau_relative_error')),'closed_hybridization':_f(closed.get('hybridization_metric')),
             'closed_mode_valid':vc,'control_mode_valid':vo,'closed_delay_valid':bool(closed.get('delay_gate_valid',False)),
             'lambda_real':_f(sc.get('lambda_real')),'lambda_imag':_f(sc.get('lambda_imag')),'omega_mode':_f(sc.get('omega_mode')),'T_mode':_f(sc.get('T_mode')),
             'group_velocity':_f(sc.get('group_velocity')),'tau_loop_group':_f(sc.get('tau_loop_group')),'tau_return_measured':_f(sc.get('tau_return_measured')),
             'phi_loop':_f(sc.get('phi_loop')),'omega_swirl_rms_core':_f(sc.get('omega_swirl_rms_core')),'mode_over_swirl_frequency_ratio':_f(sc.get('mode_over_swirl_frequency_ratio'))}
        revealed.append(rec)
        clock_rows.append({x:rec[x] for x in ('pair_id','carrier_id','profile','axial_ratio','core_fraction','m','n','both_valid','lambda_real','lambda_imag','omega_mode','T_mode','group_velocity','tau_loop_group','tau_return_measured','phi_loop','omega_swirl_rms_core','mode_over_swirl_frequency_ratio','log_growth_ratio')})
        if both and not neutral and np.isfinite(rec['closed_loop_phase']) and np.isfinite(logratio):phase_rows.append((k['carrier_id'],int(k['m']),rec['closed_loop_phase'],logratio))
    fields=list(revealed[0].keys()) if revealed else []
    with open(out/'revealed_pairs.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(revealed)
    if clock_rows:
        with open(out/'SWIRL_CLOCK.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(clock_rows[0].keys()));w.writeheader();w.writerows(clock_rows)

    # Integrity fix v0.1.1: carrier votes use ONLY both-valid, non-neutral comparisons.
    carrier_votes=[]; logtie=float(cfg.get('carrier_log_tie_abs',np.log(1.02)))
    for cid in sorted(set(x['carrier_id'] for x in revealed)):
        x=[r for r in revealed if r['carrier_id']==cid and r['both_valid'] and not r['neutral_pair'] and np.isfinite(r['log_growth_ratio'])]
        med=float(np.median([r['log_growth_ratio'] for r in x])) if x else np.nan
        vote='TIE' if not np.isfinite(med) or abs(med)<=logtie else 'CLOSED_BETTER' if med<0 else 'CONTROL_BETTER'
        carrier_votes.append({'carrier_id':cid,'n_both_valid_non_neutral':len(x),'median_log_closed_over_control_growth':med,'vote':vote,'closed_better':vote=='CLOSED_BETTER'})
    usable=[x for x in carrier_votes if x['vote']!='TIE'];ksum=sum(x['vote']=='CLOSED_BETTER' for x in usable);p=_binom_tail(ksum,len(usable)); finite_meds=[x['median_log_closed_over_control_growth'] for x in carrier_votes if np.isfinite(x['median_log_closed_over_control_growth'])];effect=float(np.exp(np.median(finite_meds))) if finite_meds else np.nan

    # Generic phase predictive gate; always both-valid only.
    if phase_rows:
        groups=np.array([x[0] for x in phase_rows]);phi=np.array([x[2] for x in phase_rows]);y=np.array([x[3] for x in phase_rows]);cv=circular_regression_cv(phi,y,groups)
        rng=np.random.default_rng(int(cfg.get('permutation_seed',8675309)));null=[]
        for _ in range(int(cfg.get('phase_permutations',499))):
            pp=phi.copy()
            for gg in np.unique(groups):
                ii=np.where(groups==gg)[0]; vv=pp[ii].copy(); rng.shuffle(vv); pp[ii]=vv
            null.append(circular_regression_cv(pp,y,groups)['cv_r2'])
        pperm=(1+sum(np.isfinite(z) and z>=cv['cv_r2'] for z in null))/(1+len(null)) if np.isfinite(cv['cv_r2']) else 1.0
    else:cv={'cv_r2':np.nan,'rmse':np.nan,'n':0};pperm=1.0

    # Branch diagnostics, preregistration may choose m=1 as primary and m=2 as negative control.
    branch={}
    for mm in sorted(set(x[1] for x in phase_rows)):
        rr=[x for x in phase_rows if x[1]==mm];groups=np.array([x[0] for x in rr]);phi=np.array([x[2] for x in rr]);y=np.array([x[3] for x in rr]);branch[str(mm)]=circular_regression_cv(phi,y,groups)

    # Delay integrity fix: valid CLOSED modes with a valid measured-return diagnostic only.
    taus=np.array([r['closed_tau_error'] for r in revealed if r['closed_mode_valid'] and r['closed_delay_valid'] and np.isfinite(r['closed_tau_error'])],float);delay_med=float(np.median(taus)) if len(taus) else np.nan
    mode_fraction=float(np.mean([bool(x['closed_mode_valid']) for x in revealed])) if revealed else 0.
    closure_pass=bool(len(usable)>=int(cfg.get('closure_min_carriers',4)) and p<=float(cfg.get('closure_sign_alpha',.05)) and effect<=float(cfg.get('closure_effect_ratio_max',.90)))
    phase_pass=bool(np.isfinite(cv['cv_r2']) and cv['cv_r2']>=float(cfg.get('phase_cv_r2_min',.15)) and pperm<=float(cfg.get('phase_perm_alpha',.05)))
    delay_pass=bool(np.isfinite(delay_med) and delay_med<=float(cfg.get('delay_relative_error_max',.25)))
    mode_pass=bool(mode_fraction>=float(cfg.get('mode_valid_fraction_min',.70)))

    target_test=None;target_pass=False
    if 'confirmatory_phase_target_rad' in cfg:
        target_test=_target_phase_carrier_test(revealed,float(cfg['confirmatory_phase_target_rad']),int(cfg.get('confirmatory_m',1)),int(cfg.get('confirmatory_min_rows_per_carrier',4)))
        target_pass=bool(target_test['n_carriers']>=int(cfg.get('confirmatory_min_carriers',6)) and target_test['one_sided_sign_p']<=float(cfg.get('confirmatory_phase_alpha',.05)) and target_test['median_carrier_slope']<0)

    role=str(cfg.get('campaign_role','generic'))
    if role=='confirmatory_m1': verdict='SUPPORTS_M1_SWIRL_CLOCK_PHASE_GATE' if all((target_pass,delay_pass,mode_pass)) else 'M1_CONFIRMATORY_NOT_ESTABLISHED'
    elif role=='negative_control_m2': verdict='M2_NEGATIVE_CONTROL_CLEAR' if not target_pass else 'M2_UNEXPECTED_TARGET_PHASE_SIGNAL'
    else: verdict='SUPPORTS_SELF_GENERATED_PHASE_FEEDBACK_MECHANISM' if all((closure_pass,phase_pass,delay_pass,mode_pass)) else 'MECHANISM_NOT_ESTABLISHED'

    summary={'format':'SST-FINITE-CORE-REVEAL-1.1','n_pairs':len(revealed),'n_carriers':len(carrier_votes),'n_carriers_non_tie':len(usable),'carrier_closed_better':ksum,'carrier_sign_p_one_sided':p,'median_closed_over_symmetric_control_growth_ratio':effect,'closure_advantage_gate':closure_pass,
             'finite_core_mode_valid_fraction':mode_fraction,'finite_core_mode_gate':mode_pass,'median_group_vs_wavepacket_delay_relative_error_valid_only':delay_med,'self_generated_delay_gate':delay_pass,
             'phase_effect_cv_r2':cv['cv_r2'],'phase_effect_permutation_p':pperm,'phase_predictive_gate':phase_pass,'phase_branch_cv':branch,
             'confirmatory_phase_target_test':target_test,'confirmatory_phase_target_gate':target_pass,'campaign_role':role,
             'explicit_delay_parameter_used':False,'target_phase_used_in_dynamics':False,'symmetric_k_control_used':True,'verdict':verdict,'carrier_votes':carrier_votes}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    lines=['# Conclusions','',f'**Verdict:** `{verdict}`','',f'- finite-core mode valid fraction: {mode_fraction:.3f}',f'- median valid-only measured-delay error: {delay_med:.4g}',f'- carrier-level closed-loop sign p (both-valid, non-neutral only): {p:.4g}',f'- median CLOSED / symmetric-control growth ratio: {effect:.4g}',f'- phase-effect leave-one-carrier-out CV R²: {cv["cv_r2"]:.4g}',f'- grouped phase permutation p: {pperm:.4g}']
    if target_test:lines += [f'- preregistered phase target: {target_test["target_phase_rad"]:.4g} rad',f'- target-phase carrier direction p: {target_test["one_sided_sign_p"]:.4g}',f'- target-phase median carrier slope: {target_test["median_carrier_slope"]:.4g}']
    lines += ['','No delay is supplied to the dynamics. Group delay and return delay are measured outputs. v0.1.1 uses a symmetric ±Δk control to remove first-order dispersion-slope bias.']
    (out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return summary
