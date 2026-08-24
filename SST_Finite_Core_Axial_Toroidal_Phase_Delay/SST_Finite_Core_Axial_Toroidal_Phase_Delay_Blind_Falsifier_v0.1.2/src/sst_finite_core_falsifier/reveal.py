from __future__ import annotations
from pathlib import Path
import csv,json,math,shutil
import numpy as np
from .seal import verify
from .delay import circular_regression_cv,wrap,wrap_positive


def _binom_tail(k,n):return sum(math.comb(n,j) for j in range(k,n+1))/(2**n) if n else 1.0

def _f(x,default=np.nan):
    try:return float(x)
    except Exception:return float(default)

def _bounded_growth_effect(gc,go,floor):
    """Bounded CLOSED-vs-control response in [-1,1]; negative = CLOSED better.

    This replaces log-ratio as the primary phase response because exact/near-neutral
    modes otherwise create arbitrarily large leverage despite tiny absolute growth.
    """
    if not (np.isfinite(gc) and np.isfinite(go)): return np.nan
    return float((gc-go)/(abs(gc)+abs(go)+2.0*float(floor)))

def _target_phase_carrier_test(rows,target,m_target=1,min_rows=4):
    """Legacy compatibility only; v0.1.2 discovery presets do not use a target."""
    votes=[]
    for cid in sorted(set(r['carrier_id'] for r in rows)):
        rr=[r for r in rows if r['carrier_id']==cid and int(r['m'])==int(m_target) and r['both_valid'] and r.get('closed_phase_valid',True) and not r['neutral_pair'] and np.isfinite(r['closed_loop_phase']) and np.isfinite(r.get('growth_effect_bounded',r.get('log_growth_ratio',np.nan)))]
        if len(rr)<int(min_rows):continue
        x=np.array([np.cos(wrap(r['closed_loop_phase']-target)) for r in rr],float); y=np.array([r.get('growth_effect_bounded',r.get('log_growth_ratio',np.nan)) for r in rr],float)
        if np.ptp(x)<1e-5:continue
        X=np.c_[np.ones(len(x)),x]; q=np.linalg.lstsq(X,y,rcond=None)[0]; pred=X@q; den=float(np.sum((y-y.mean())**2)); r2=1-float(np.sum((y-pred)**2))/max(den,1e-30)
        slope=float(q[1]); votes.append({'carrier_id':cid,'n':len(rr),'target_phase_slope':slope,'r2':r2,'direction_correct':slope<0})
    k=sum(v['direction_correct'] for v in votes); n=len(votes); p=_binom_tail(k,n); med=float(np.median([v['target_phase_slope'] for v in votes])) if votes else np.nan
    return {'target_phase_rad':float(target),'m_target':int(m_target),'n_carriers':n,'direction_correct_carriers':k,'one_sided_sign_p':p,'median_carrier_slope':med,'carrier_votes':votes,'legacy_only':True}

def _phase_fit(phi,y):
    phi=np.asarray(phi,float); y=np.asarray(y,float)
    if len(phi)<4:return {'available':False,'n':len(phi)}
    X=np.c_[np.ones(len(phi)),np.cos(phi),np.sin(phi)]; q=np.linalg.lstsq(X,y,rcond=None)[0]; pred=X@q; den=float(np.sum((y-y.mean())**2)); r2=1-float(np.sum((y-pred)**2))/max(den,1e-30)
    b=float(q[1]); c=float(q[2]); amp=float(np.hypot(b,c)); phi_min=wrap_positive(np.arctan2(c,b)+np.pi)
    return {'available':True,'n':len(phi),'intercept':float(q[0]),'cos_coeff':b,'sin_coeff':c,'amplitude':amp,'phase_min_rad':phi_min,'r2':float(r2)}

def _phase_discovery(rows,m_target,regime,cfg):
    rr=[r for r in rows if int(r['m'])==int(m_target) and r['both_valid'] and r['closed_phase_valid'] and not r['neutral_pair'] and r['clock_regime']==regime and np.isfinite(r['closed_loop_phase']) and np.isfinite(r['growth_effect_bounded'])]
    carriers=sorted(set(r['carrier_id'] for r in rr)); minrows=int(cfg.get('phase_discovery_min_rows_per_carrier',3))
    keep=[]
    for c in carriers:
        cc=[r for r in rr if r['carrier_id']==c]
        if len(cc)>=minrows:keep.extend(cc)
    rr=keep; carriers=sorted(set(r['carrier_id'] for r in rr))
    if not rr:return {'available':False,'m_target':int(m_target),'clock_regime':regime,'n_rows':0,'n_carriers':0}
    phi=np.array([r['closed_loop_phase'] for r in rr],float); y=np.array([r['growth_effect_bounded'] for r in rr],float); groups=np.array([r['carrier_id'] for r in rr])
    # Remove carrier baselines before discovery so geometry-specific growth offsets
    # cannot set the global phase minimum.
    yc=y.copy()
    for g in np.unique(groups):
        ii=np.where(groups==g)[0]; yc[ii]-=np.mean(yc[ii])
    fit=_phase_fit(phi,yc); cv=circular_regression_cv(phi,yc,groups)
    rng=np.random.default_rng(int(cfg.get('phase_discovery_seed',271828)))
    nperm=int(cfg.get('phase_permutations',499)); null=[]
    for _ in range(nperm):
        pp=phi.copy()
        for gg in np.unique(groups):
            ii=np.where(groups==gg)[0]; vv=pp[ii].copy(); rng.shuffle(vv); pp[ii]=vv
        null.append(circular_regression_cv(pp,yc,groups)['cv_r2'])
    pperm=(1+sum(np.isfinite(z) and z>=cv['cv_r2'] for z in null))/(1+nperm) if np.isfinite(cv['cv_r2']) else 1.0
    # Carrier bootstrap gives a circular stability diagnostic for the discovered
    # phase; it is explicitly discovery uncertainty, not a confirmatory CI.
    phboot=[]; nboot=int(cfg.get('phase_discovery_bootstrap',499)); uc=list(np.unique(groups))
    if len(uc)>=2:
        for _ in range(nboot):
            draw=rng.choice(uc,size=len(uc),replace=True); bp=[]; by=[]
            for g in draw:
                ii=np.where(groups==g)[0]; bp.extend(phi[ii]); by.extend(yc[ii])
            ff=_phase_fit(np.asarray(bp),np.asarray(by))
            if ff.get('available'):phboot.append(ff['phase_min_rad'])
    if phboot:
        z=np.mean(np.exp(1j*np.asarray(phboot))); R=float(abs(z)); circ_sd=float(np.sqrt(max(-2*np.log(max(R,1e-12)),0.0)))
    else:R=np.nan;circ_sd=np.nan
    return {'available':bool(fit.get('available')),'m_target':int(m_target),'clock_regime':regime,'n_rows':len(rr),'n_carriers':len(carriers),'carriers':carriers,'fit':fit,'leave_one_carrier_out_cv':cv,'grouped_phase_permutation_p':float(pperm),'bootstrap_n':len(phboot),'bootstrap_resultant_length':R,'bootstrap_circular_sd_rad':circ_sd,'discovery_only':True}

def reveal(root,blind,catalog,config,private,outdir):
    verify(root,blind,catalog,config);blind=Path(blind);catalog=Path(catalog);private=Path(private);out=Path(outdir)
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True,exist_ok=True);cfg=json.loads(Path(config).read_text(encoding='utf-8'));keys={x['pair_id']:x for x in json.loads((private/'pair_key.json').read_text(encoding='utf-8'))};rows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));case_dir=blind/'cases';revealed=[];phase_rows=[];clock_rows=[]
    eps=float(cfg.get('neutral_growth_epsilon',1e-8)); eff_floor=float(cfg.get('growth_effect_floor',max(eps,1e-6)))
    for row in rows:
        k=keys[row['pair_id']]; mapping={k['candidate_a']:k['condition_a'],k['candidate_b']:k['condition_b']}; win=row.get('winner_anonymous'); win_cand=k['candidate_a'] if win=='A' else k['candidate_b'] if win=='B' else None; wincond=mapping.get(win_cand,win)
        ca=json.loads((case_dir/f"{k['candidate_a']}.json").read_text(encoding='utf-8'));cb=json.loads((case_dir/f"{k['candidate_b']}.json").read_text(encoding='utf-8')); bycond={k['condition_a']:ca,k['condition_b']:cb};closed=bycond['CLOSED'];ctrl=bycond.get('SYMMETRIC_CONTROL',bycond.get('OFFSET_CONTROL'))
        gc=_f(closed.get('growth_metric'));go=_f(ctrl.get('growth_metric')); vc=bool(closed.get('eigenmode_gate_valid')); vo=bool(ctrl.get('eigenmode_gate_valid')); both=bool(vc and vo)
        neutral=bool(both and np.isfinite(gc) and np.isfinite(go) and max(gc,go)<=eps)
        logratio=float(np.log((gc+eps)/(go+eps))) if both and np.isfinite(gc) and np.isfinite(go) and not neutral else 0.0 if neutral else np.nan
        ratio=float(np.exp(logratio)) if np.isfinite(logratio) else np.nan
        geff=_bounded_growth_effect(gc,go,eff_floor) if both and not neutral else 0.0 if neutral else np.nan
        sc=closed.get('swirl_clock',{}) if isinstance(closed.get('swirl_clock',{}),dict) else {}
        cont=closed.get('dispersion',{}).get('axial_branch_continuation',{}) if isinstance(closed.get('dispersion',{}),dict) else {}
        rec={**k,'winner_condition':wincond,'closed_growth':gc,'control_growth':go,'closed_over_control_growth':ratio,'log_growth_ratio':logratio,'growth_effect_bounded':geff,'neutral_pair':neutral,'both_valid':both,
             'closed_loop_phase':_f(closed.get('loop_phase')),'closed_tau_error':_f(closed.get('tau_relative_error')),'closed_hybridization':_f(closed.get('hybridization_metric')),
             'closed_mode_valid':vc,'control_mode_valid':vo,'closed_delay_valid':bool(closed.get('delay_gate_valid',False)),'closed_phase_valid':bool(closed.get('phase_gate_valid',False)),
             'phase_uncertainty_rad':_f(sc.get('phase_uncertainty_rad')),'phase_sampling_step_rad':_f(sc.get('phase_sampling_step_rad')),'dispersion_omega_rmse':_f(sc.get('dispersion_omega_rmse')),'carrier_phase_cycles_at_return':_f(sc.get('carrier_phase_cycles_at_return')),
             'lambda_real':_f(sc.get('lambda_real')),'lambda_imag':_f(sc.get('lambda_imag')),'omega_mode':_f(sc.get('omega_mode')),'T_mode':_f(sc.get('T_mode')),
             'advective_frequency_mode_weighted':_f(sc.get('advective_frequency_mode_weighted')),'omega_intrinsic':_f(sc.get('omega_intrinsic')),'T_intrinsic':_f(sc.get('T_intrinsic')),
             'group_velocity':_f(sc.get('group_velocity')),'tau_loop_group':_f(sc.get('tau_loop_group')),'tau_return_measured':_f(sc.get('tau_return_measured')),
             'phi_loop':_f(sc.get('phi_loop')),'omega_swirl_rms_core':_f(sc.get('omega_swirl_rms_core')),'mode_over_swirl_frequency_ratio':_f(sc.get('mode_over_swirl_frequency_ratio')),'intrinsic_over_swirl_frequency_ratio':_f(sc.get('intrinsic_over_swirl_frequency_ratio')),
             'clock_regime':str(sc.get('clock_regime',closed.get('clock_regime','UNKNOWN'))),'axial_branch_continuation_enabled':bool(cont.get('enabled',False)),'axial_branch_continuation_success':bool(cont.get('success',not cont.get('enabled',False)))}
        revealed.append(rec)
        clock_fields=('pair_id','carrier_id','profile','axial_ratio','core_fraction','m','n','both_valid','closed_phase_valid','clock_regime','lambda_real','lambda_imag','omega_mode','T_mode','advective_frequency_mode_weighted','omega_intrinsic','T_intrinsic','group_velocity','tau_loop_group','tau_return_measured','phi_loop','phase_uncertainty_rad','phase_sampling_step_rad','dispersion_omega_rmse','carrier_phase_cycles_at_return','omega_swirl_rms_core','mode_over_swirl_frequency_ratio','intrinsic_over_swirl_frequency_ratio','growth_effect_bounded','log_growth_ratio')
        clock_rows.append({x:rec[x] for x in clock_fields})
        if both and rec['closed_phase_valid'] and not neutral and np.isfinite(rec['closed_loop_phase']) and np.isfinite(geff):phase_rows.append((k['carrier_id'],int(k['m']),rec['clock_regime'],rec['closed_loop_phase'],geff))
    fields=list(revealed[0].keys()) if revealed else []
    with open(out/'revealed_pairs.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(revealed)
    if clock_rows:
        with open(out/'SWIRL_CLOCK.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(clock_rows[0].keys()));w.writeheader();w.writerows(clock_rows)

    carrier_votes=[]; effect_tie=float(cfg.get('carrier_bounded_tie_abs',.02))
    for cid in sorted(set(x['carrier_id'] for x in revealed)):
        x=[r for r in revealed if r['carrier_id']==cid and r['both_valid'] and not r['neutral_pair'] and np.isfinite(r['growth_effect_bounded'])]
        med=float(np.median([r['growth_effect_bounded'] for r in x])) if x else np.nan
        logr=float(np.median([r['log_growth_ratio'] for r in x if np.isfinite(r['log_growth_ratio'])])) if x else np.nan
        vote='TIE' if not np.isfinite(med) or abs(med)<=effect_tie else 'CLOSED_BETTER' if med<0 else 'CONTROL_BETTER'
        carrier_votes.append({'carrier_id':cid,'n_both_valid_non_neutral':len(x),'median_bounded_growth_effect':med,'median_log_closed_over_control_growth_diagnostic':logr,'vote':vote,'closed_better':vote=='CLOSED_BETTER'})
    usable=[x for x in carrier_votes if x['vote']!='TIE'];ksum=sum(x['vote']=='CLOSED_BETTER' for x in usable);p=_binom_tail(ksum,len(usable)); finite_eff=[x['median_bounded_growth_effect'] for x in carrier_votes if np.isfinite(x['median_bounded_growth_effect'])];effect_bounded=float(np.median(finite_eff)) if finite_eff else np.nan
    finite_logs=[x['median_log_closed_over_control_growth_diagnostic'] for x in carrier_votes if np.isfinite(x['median_log_closed_over_control_growth_diagnostic'])];effect=float(np.exp(np.median(finite_logs))) if finite_logs else np.nan

    if phase_rows:
        groups=np.array([x[0] for x in phase_rows]);phi=np.array([x[3] for x in phase_rows]);y=np.array([x[4] for x in phase_rows]);cv=circular_regression_cv(phi,y,groups)
        rng=np.random.default_rng(int(cfg.get('permutation_seed',8675309)));null=[]
        for _ in range(int(cfg.get('phase_permutations',499))):
            pp=phi.copy()
            for gg in np.unique(groups):
                ii=np.where(groups==gg)[0]; vv=pp[ii].copy(); rng.shuffle(vv); pp[ii]=vv
            null.append(circular_regression_cv(pp,y,groups)['cv_r2'])
        pperm=(1+sum(np.isfinite(z) and z>=cv['cv_r2'] for z in null))/(1+len(null)) if np.isfinite(cv['cv_r2']) else 1.0
    else:cv={'cv_r2':np.nan,'rmse':np.nan,'n':0};pperm=1.0

    branch={}
    for mm in sorted(set(x[1] for x in phase_rows)):
        for regime in sorted(set(x[2] for x in phase_rows if x[1]==mm)):
            rr=[x for x in phase_rows if x[1]==mm and x[2]==regime]; groups=np.array([x[0] for x in rr]);phi=np.array([x[3] for x in rr]);y=np.array([x[4] for x in rr]);branch[f'm{mm}:{regime}']=circular_regression_cv(phi,y,groups)

    taus=np.array([r['closed_tau_error'] for r in revealed if r['closed_mode_valid'] and r['closed_delay_valid'] and np.isfinite(r['closed_tau_error'])],float);delay_med=float(np.median(taus)) if len(taus) else np.nan
    phase_unc=np.array([r['phase_uncertainty_rad'] for r in revealed if r['closed_delay_valid'] and np.isfinite(r['phase_uncertainty_rad'])],float); phase_unc_med=float(np.median(phase_unc)) if len(phase_unc) else np.nan
    mode_fraction=float(np.mean([bool(x['closed_mode_valid']) for x in revealed])) if revealed else 0.
    delay_rows=[r for r in revealed if r['closed_mode_valid'] and r['closed_delay_valid']]; phase_fraction=float(np.mean([r['closed_phase_valid'] for r in delay_rows])) if delay_rows else 0.
    regime_counts={z:sum(r['closed_phase_valid'] and r['clock_regime']==z for r in revealed) for z in ('FAST_SWIRL_LOCKED','SLOW_MODE','OTHER_BRANCH')}
    closure_pass=bool(len(usable)>=int(cfg.get('closure_min_carriers',4)) and p<=float(cfg.get('closure_sign_alpha',.05)) and np.isfinite(effect_bounded) and effect_bounded<=float(cfg.get('closure_bounded_effect_max',-.05)))
    phase_pass=bool(np.isfinite(cv['cv_r2']) and cv['cv_r2']>=float(cfg.get('phase_cv_r2_min',.15)) and pperm<=float(cfg.get('phase_perm_alpha',.05)))
    delay_pass=bool(np.isfinite(delay_med) and delay_med<=float(cfg.get('delay_relative_error_max',.25)))
    mode_pass=bool(mode_fraction>=float(cfg.get('mode_valid_fraction_min',.70)))
    phase_measurement_pass=bool(phase_fraction>=float(cfg.get('phase_valid_fraction_min',.35)))

    target_test=None;target_pass=False
    if 'confirmatory_phase_target_rad' in cfg:
        target_test=_target_phase_carrier_test(revealed,float(cfg['confirmatory_phase_target_rad']),int(cfg.get('confirmatory_m',1)),int(cfg.get('confirmatory_min_rows_per_carrier',4)))
        target_pass=bool(target_test['n_carriers']>=int(cfg.get('confirmatory_min_carriers',6)) and target_test['one_sided_sign_p']<=float(cfg.get('confirmatory_phase_alpha',.05)) and target_test['median_carrier_slope']<0)

    role=str(cfg.get('campaign_role','generic')); discovery=None
    if role in ('phase_discovery_m1','phase_diagnostic_m2'):
        mm=1 if role=='phase_discovery_m1' else 2; reg=str(cfg.get('phase_discovery_primary_regime','FAST_SWIRL_LOCKED' if mm==1 else 'OTHER_BRANCH'))
        discovery=_phase_discovery(revealed,mm,reg,cfg)
        (out/'PHASE_DISCOVERY.json').write_text(json.dumps(discovery,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
        enough=bool(discovery.get('n_carriers',0)>=int(cfg.get('phase_discovery_min_carriers',5)) and discovery.get('n_rows',0)>=int(cfg.get('phase_discovery_min_rows_total',20)))
        verdict=('M1_PHASE_DISCOVERY_COMPLETE' if mm==1 else 'M2_PHASE_DIAGNOSTIC_COMPLETE') if all((delay_pass,mode_pass,phase_measurement_pass,enough)) else ('M1_PHASE_DISCOVERY_INCOMPLETE' if mm==1 else 'M2_PHASE_DIAGNOSTIC_INCOMPLETE')
    elif role=='confirmatory_m1': verdict='SUPPORTS_M1_SWIRL_CLOCK_PHASE_GATE' if all((target_pass,delay_pass,mode_pass,phase_measurement_pass)) else 'M1_CONFIRMATORY_NOT_ESTABLISHED'
    elif role=='negative_control_m2': verdict='M2_NEGATIVE_CONTROL_CLEAR' if not target_pass else 'M2_UNEXPECTED_TARGET_PHASE_SIGNAL'
    else: verdict='SUPPORTS_SELF_GENERATED_PHASE_FEEDBACK_MECHANISM' if all((closure_pass,phase_pass,delay_pass,mode_pass,phase_measurement_pass)) else 'MECHANISM_NOT_ESTABLISHED'

    summary={'format':'SST-FINITE-CORE-REVEAL-1.2','n_pairs':len(revealed),'n_carriers':len(carrier_votes),'n_carriers_non_tie':len(usable),'carrier_closed_better':ksum,'carrier_sign_p_one_sided':p,'median_closed_over_symmetric_control_growth_ratio_diagnostic':effect,'median_bounded_closed_vs_control_growth_effect':effect_bounded,'closure_advantage_gate':closure_pass,
             'finite_core_mode_valid_fraction':mode_fraction,'finite_core_mode_gate':mode_pass,'median_group_vs_wavepacket_delay_relative_error_valid_only':delay_med,'self_generated_delay_gate':delay_pass,
             'phase_measurement_valid_fraction_among_delay_valid':phase_fraction,'phase_measurement_gate':phase_measurement_pass,'median_phase_uncertainty_rad':phase_unc_med,'phase_valid_regime_counts':regime_counts,
             'phase_effect_cv_r2':cv['cv_r2'],'phase_effect_permutation_p':pperm,'phase_predictive_gate':phase_pass,'phase_branch_regime_cv':branch,
             'confirmatory_phase_target_test':target_test,'confirmatory_phase_target_gate':target_pass,'phase_discovery':discovery,'campaign_role':role,
             'explicit_delay_parameter_used':False,'target_phase_used_in_dynamics':False,'symmetric_k_control_used':True,'bounded_growth_effect_used_for_phase':True,'phase_observable_version':'continuous_return_v2','verdict':verdict,'carrier_votes':carrier_votes}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    lines=['# Conclusions','',f'**Verdict:** `{verdict}`','',f'- finite-core mode valid fraction: {mode_fraction:.3f}',f'- median valid-only measured-delay error: {delay_med:.4g}',f'- phase-measurement valid fraction: {phase_fraction:.3f}',f'- median phase uncertainty: {phase_unc_med:.4g} rad',f'- carrier-level closed-loop sign p (both-valid, non-neutral only): {p:.4g}',f'- median bounded CLOSED-vs-control growth effect: {effect_bounded:.4g}',f'- phase-effect leave-one-carrier-out CV R²: {cv["cv_r2"]:.4g}',f'- grouped phase permutation p: {pperm:.4g}']
    if discovery and discovery.get('available'):
        lines += [f'- discovery regime: m={discovery["m_target"]}, {discovery["clock_regime"]}',f'- discovery phase minimum: {discovery["fit"]["phase_min_rad"]:.5g} rad',f'- discovery bootstrap circular SD: {discovery["bootstrap_circular_sd_rad"]:.4g} rad','- this phase is **discovery only** and must be frozen in a later independent release before confirmation.']
    if target_test:lines += [f'- legacy preregistered phase target: {target_test["target_phase_rad"]:.4g} rad',f'- target-phase carrier direction p: {target_test["one_sided_sign_p"]:.4g}',f'- target-phase median carrier slope: {target_test["median_carrier_slope"]:.4g}']
    lines += ['','No delay is supplied to the dynamics. v0.1.2 refines the packet return continuously, gates phase by measured numerical/dispersion uncertainty, reports intrinsic frequency, and uses bounded growth response for phase statistics.']
    (out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return summary
