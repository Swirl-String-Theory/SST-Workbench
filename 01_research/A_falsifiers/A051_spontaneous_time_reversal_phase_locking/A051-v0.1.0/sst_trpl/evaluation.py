from __future__ import annotations
import math
from collections import defaultdict
import numpy as np
from .observables import phase_lock_metrics, chi_t, gauge_rotate, time_reverse_conjugate

PASS='PASS'; FAIL='FAIL'; INDET='INDETERMINATE'; SKIP='SKIP'

def _gate(status, **kw): return {'status':status, **kw}

def exact_binom_two_sided(k,n,p=0.5):
    if n<=0: return float('nan')
    probs=[math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(n+1)]
    pk=probs[k]
    return min(1.0,sum(x for x in probs if x<=pk+1e-15))

def evaluate(manifest, t, eta, energy, config, residual=None):
    th=config['thresholds']; eps=float(config.get('epsilon',1e-15)); burn=float(config.get('burnin_fraction',0.25))
    runs=manifest.get('runs',[]); gates={}; details={}
    nr=len(runs)
    valid=(manifest.get('schema')=='TRPL_INPUT_V1' and eta.shape==(nr,t.size,2) and energy.shape==(nr,t.size)
           and np.all(np.isfinite(t)) and np.all(np.diff(t)>0) and np.all(np.isfinite(eta.real)) and np.all(np.isfinite(eta.imag)) and np.all(np.isfinite(energy)))
    gates['G0_INPUT_CONTRACT']=_gate(PASS if valid else FAIL,n_runs=nr,n_t=int(t.size))
    if not valid: return finalize(manifest,gates,details)
    cond=manifest.get('conditions',{}); prod=manifest.get('producer',{})
    unbiased=(cond.get('external_forcing') is False and cond.get('time_odd_bias') is False)
    gates['G1_UNFORCED_UNBIASED']=_gate(PASS if unbiased else FAIL,external_forcing=cond.get('external_forcing'),time_odd_bias=cond.get('time_odd_bias'))
    phase_ok=(cond.get('material_phase_observable') is True and cond.get('phase_derived_from_centerline_only') is False)
    gates['G2_INDEPENDENT_PHASE_OBSERVABLE']=_gate(PASS if phase_ok else INDET,material_phase_observable=cond.get('material_phase_observable'),phase_derived_from_centerline_only=cond.get('phase_derived_from_centerline_only'))
    # gauge and antiunitary algebra are evaluator qualification guards
    probe=eta[0,::max(1,t.size//100)]
    c0=chi_t(probe,eps); c1=chi_t(gauge_rotate(probe,0.731),eps); ct=chi_t(time_reverse_conjugate(probe),eps)
    gauge_err=float(np.max(np.abs(c0-c1))); tr_err=float(np.max(np.abs(c0+ct)))
    gates['Q1_GAUGE_INVARIANCE']=_gate(PASS if gauge_err<1e-12 else FAIL,max_abs_error=gauge_err)
    gates['Q2_TIME_ODD_ALGEBRA']=_gate(PASS if tr_err<1e-12 else FAIL,max_abs_error=tr_err)
    metrics=[]
    for i,r in enumerate(runs):
        m=phase_lock_metrics(t,eta[i],burn,eps); m['run_id']=r.get('run_id',str(i)); m['pair_id']=r.get('pair_id'); m['pair_role']=r.get('pair_role')
        i0=min(max(int(round(burn*t.size)),0),t.size-1)
        m['energy_mean']=float(np.mean(energy[i,i0:])); m['energy_span_rel']=float((np.max(energy[i])-np.min(energy[i]))/(abs(np.mean(energy[i]))+eps))
        if residual is not None: m['residual_mean']=float(np.mean(np.abs(residual[i,i0:])))
        m['locked']=(m['status']=='OK' and m['mean_weight']>=th['min_mode_weight'] and m['coherence']>=th['min_phase_coherence'] and abs(m['chi_mean'])>=th['min_abs_chi'] and m['phase_drift_per_window_rad']<=th['max_phase_drift_per_window_rad'])
        metrics.append(m)
    details['run_metrics']=metrics
    support=[m['mean_weight'] for m in metrics if np.isfinite(m.get('mean_weight',np.nan))]
    gates['G3_MODE_SUPPORT']=_gate(PASS if support and float(np.median(support))>=th['min_mode_weight'] else FAIL,median_weight=float(np.median(support)) if support else 0.0)
    locked=[m for m in metrics if m['locked']]; frac=len(locked)/nr if nr else 0.0
    gates['G4_LOCKED_NONZERO_ORDER']=_gate(PASS if frac>=th['min_locked_fraction'] else FAIL,locked_fraction=frac,n_locked=len(locked),n_runs=nr)
    bypair=defaultdict(dict)
    for i,r in enumerate(runs): bypair[r.get('pair_id')][r.get('pair_role')]=(i,metrics[i])
    pairrows=[]
    for pid,p in bypair.items():
        if 'A' not in p or 'B' not in p: continue
        ia,a=p['A']; ib,b=p['B']; ca=a['chi_mean']; cb=b['chi_mean']
        magdiff=abs(abs(ca)-abs(cb))/(max(abs(ca),abs(cb),eps)); chisum=abs(ca+cb)
        ea,eb=a['energy_mean'],b['energy_mean']; esplit=abs(ea-eb)/(max(abs(ea),abs(eb),eps))
        row={'pair_id':pid,'chi_a':ca,'chi_b':cb,'chi_sum_abs':chisum,'magnitude_rel_diff':magdiff,'energy_split_rel':esplit}
        row['antisym_pass']=chisum<=th['max_pair_chi_sum_abs'] and magdiff<=th['max_pair_magnitude_rel_diff']
        row['degenerate_pass']=esplit<=th['max_energy_split_rel']
        pairrows.append(row)
    details['pair_metrics']=pairrows
    gates['G5_TR_PAIR_ANTISYMMETRY']=_gate(PASS if pairrows and all(x['antisym_pass'] for x in pairrows) else (INDET if not pairrows else FAIL),n_pairs=len(pairrows),max_chi_sum_abs=max([x['chi_sum_abs'] for x in pairrows],default=float('nan')),max_magnitude_rel_diff=max([x['magnitude_rel_diff'] for x in pairrows],default=float('nan')))
    gates['G6_BRANCH_DEGENERACY']=_gate(PASS if pairrows and all(x['degenerate_pass'] for x in pairrows) else (INDET if not pairrows else FAIL),n_pairs=len(pairrows),max_energy_split_rel=max([x['energy_split_rel'] for x in pairrows],default=float('nan')))
    neutral=[metrics[i] for i,r in enumerate(runs) if r.get('neutral_selection') and metrics[i]['locked']]
    if len(neutral)<th['seed_balance_min_n']:
        gates['G7_SYMMETRY_NEUTRAL_BALANCE']=_gate(INDET,n=len(neutral),minimum=th['seed_balance_min_n'])
    else:
        k=sum(m['chi_mean']>0 for m in neutral); pv=exact_binom_two_sided(k,len(neutral),0.5)
        gates['G7_SYMMETRY_NEUTRAL_BALANCE']=_gate(PASS if pv>=th['seed_balance_p_min'] else FAIL,n=len(neutral),positive=k,p_value=pv)
    conv=all(cond.get(k) is True for k in ['spatial_converged','temporal_converged','core_converged'])
    gates['G8_NUMERICAL_CONVERGENCE']=_gate(PASS if conv else INDET,spatial=cond.get('spatial_converged'),temporal=cond.get('temporal_converged'),core=cond.get('core_converged'))
    groups=defaultdict(list)
    for i,r in enumerate(runs): groups[(r.get('source_group'),r.get('geometry_group'))].append(metrics[i])
    robust=0
    for _,ms in groups.items():
        signs={1 if m['chi_mean']>0 else -1 for m in ms if m['locked']}
        if signs=={-1,1}: robust+=1
    # Require at least two independent source groups, not merely multiple geometry labels from one source.
    source_ok=[]
    for s in {r.get('source_group') for r in runs}:
        sm=[metrics[i] for i,r in enumerate(runs) if r.get('source_group')==s]
        signs={1 if m['chi_mean']>0 else -1 for m in sm if m['locked']}
        if signs=={-1,1}: source_ok.append(s)
    gates['G9_SOURCE_GEOMETRY_ROBUSTNESS']=_gate(PASS if len(source_ok)>=th['min_source_groups'] else INDET,n_source_groups_passing=len(source_ok),minimum=th['min_source_groups'],robust_source_groups=sorted(str(x) for x in source_ok))
    if prod.get('time_reversal_map')!='conjugation':
        gates['G10_PRODUCER_REVERSIBILITY']=_gate(INDET,reason='producer_defined_time_reversal_map_not_implemented_in_v0.1.0')
    elif prod.get('reversibility_certified') is not True or prod.get('reversibility_residual') is None:
        gates['G10_PRODUCER_REVERSIBILITY']=_gate(INDET,reversibility_certified=prod.get('reversibility_certified'),residual=prod.get('reversibility_residual'))
    else:
        rr=float(prod['reversibility_residual']); gates['G10_PRODUCER_REVERSIBILITY']=_gate(PASS if rr<=th['max_reversibility_residual'] else FAIL,residual=rr,threshold=th['max_reversibility_residual'])
    fl=manifest.get('floquet',{})
    if fl.get('claim_stability'):
        if fl.get('certified_rpo') is not True:
            gates['G11_RPO_FLOQUET']=_gate(INDET,reason='NO_CERTIFIED_RPO')
        else:
            rho=fl.get('rho_non_neutral'); lim=fl.get('rho_limit',1.03)
            gates['G11_RPO_FLOQUET']=_gate(PASS if rho is not None and float(rho)<=float(lim) else FAIL,rho_non_neutral=rho,limit=lim)
    else:
        gates['G11_RPO_FLOQUET']=_gate(SKIP,reason='Floquet stability not claimed by primary A051 gate')
    return finalize(manifest,gates,details)

def finalize(manifest,gates,details):
    critical=['G0_INPUT_CONTRACT','G1_UNFORCED_UNBIASED','G2_INDEPENDENT_PHASE_OBSERVABLE','G3_MODE_SUPPORT','G4_LOCKED_NONZERO_ORDER','G5_TR_PAIR_ANTISYMMETRY','G6_BRANCH_DEGENERACY','G7_SYMMETRY_NEUTRAL_BALANCE','G8_NUMERICAL_CONVERGENCE','G9_SOURCE_GEOMETRY_ROBUSTNESS','G10_PRODUCER_REVERSIBILITY']
    statuses=[gates.get(k,{}).get('status',INDET) for k in critical]
    synthetic=bool(manifest.get('synthetic_reference'))
    if synthetic:
        verdict='QUALIFIED_INSTRUMENT_ONLY' if all(s==PASS for s in statuses) else 'SYNTHETIC_QUALIFICATION_FAILED'
        physics='UNTESTED_SYNTHETIC'
    elif any(s==FAIL for s in statuses):
        verdict='FAIL_TESTED_DOMAIN'; physics='FAIL_TESTED_DOMAIN'
    elif all(s==PASS for s in statuses):
        verdict='SUPPORTED_TESTED_DOMAIN'; physics='SUPPORTED_TESTED_DOMAIN'
    else:
        missing=[k for k in critical if gates.get(k,{}).get('status')!=PASS]
        verdict='INDETERMINATE_MISSING_OR_UNQUALIFIED_PREREQUISITES'; physics=verdict
        details['missing_or_unqualified']=missing
    return {'schema':'A051_TRPL_RESULT_1.0','blind':True,'synthetic_reference':synthetic,'numerics_verdict':'PASS' if gates.get('G0_INPUT_CONTRACT',{}).get('status')==PASS else 'FAIL','physics_verdict':physics,'verdict':verdict,'gates':gates,'details':details}
