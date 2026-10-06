from __future__ import annotations
import itertools
import numpy as np


def _wrap(x):
    return np.angle(np.exp(1j*np.asarray(x,float)))


def _moving_average(x, window):
    x=np.asarray(x,float); w=max(1,int(window))
    if w<=1 or len(x)<3: return x.copy()
    if w%2==0: w+=1
    pad=w//2; xp=np.pad(x,(pad,pad),mode='edge')
    return np.convolve(xp,np.ones(w,float)/w,mode='valid')


def _complex_tone_fit(t,z,omegas):
    t=np.asarray(t,float); z=np.asarray(z,complex)
    cols=[np.ones(len(t),complex)]+[np.exp(1j*float(w)*t) for w in omegas]
    X=np.column_stack(cols); beta,_,_,_=np.linalg.lstsq(X,z,rcond=None)
    pred=X@beta; resid=z-pred; rss=float(np.sum(np.abs(resid)**2))
    n=max(len(t),1); nobs=2*n; k=2*len(beta)+len(omegas)
    bic=float(nobs*np.log(max(rss/nobs,np.finfo(float).tiny))+k*np.log(max(nobs,2)))
    signal_rms=float(np.sqrt(np.mean(np.abs(z-np.mean(z))**2)))
    nrmse=float(np.sqrt(rss/n)/max(signal_rms,1e-15))
    return {'omegas':[float(w) for w in omegas],'complex_amplitudes_abs':[float(abs(b)) for b in beta[1:]],'complex_amplitudes_phase':[float(np.angle(b)) for b in beta[1:]],'offset_abs':float(abs(beta[0])),'rss':rss,'bic':bic,'nrmse':nrmse}


def _spectral_candidates(t,z,count,min_sep_bins):
    t=np.asarray(t,float); z=np.asarray(z,complex); n=len(t)
    if n<8: return [],float('nan')
    dt=float(np.median(np.diff(t))); win=np.hanning(n); y=(z-np.mean(z))*win
    sp=np.abs(np.fft.fft(y))**2; om=2*np.pi*np.fft.fftfreq(n,d=dt); dw=2*np.pi/(n*dt)
    order=np.argsort(sp)[::-1]; chosen=[]; span=max(t[-1]-t[0],dt); wmin=2*np.pi/span
    for ix in order:
        w=float(om[ix])
        if abs(w)<wmin: continue
        if all(abs(w-q)>=float(min_sep_bins)*dw for q in chosen): chosen.append(w)
        if len(chosen)>=int(count): break
    return chosen,float(dw)


def _refine_single_frequencies(t,z,candidates,dw,refine_points):
    out=[]; offsets=np.linspace(-0.5,0.5,max(3,int(refine_points)))
    for w0 in candidates:
        fits=[_complex_tone_fit(t,z,[w0+d*dw]) for d in offsets]
        out.append(float(min(fits,key=lambda r:r['rss'])['omegas'][0]))
    return out


def two_tone_metrics(times, coeff, cfg):
    t=np.asarray(times,float); z=np.asarray(coeff,complex)
    if len(t)<64: return {'support':False,'status':'INSUFFICIENT_SAMPLES'}
    cand,dw=_spectral_candidates(t,z,cfg['spectral_candidate_count'],cfg['spectral_peak_separation_bins'])
    if not cand: return {'support':False,'status':'NO_SPECTRAL_CANDIDATE'}
    cand=_refine_single_frequencies(t,z,cand,dw,cfg['spectral_refine_points'])
    one=min([_complex_tone_fit(t,z,[w]) for w in cand],key=lambda r:r['rss'])
    pairs=[_complex_tone_fit(t,z,[a,b]) for a,b in itertools.combinations(cand,2) if abs(a-b)>=float(cfg['spectral_peak_separation_bins'])*dw]
    if not pairs: return {'support':False,'status':'NO_TWO_TONE_PAIR','one_tone':one}
    two=min(pairs,key=lambda r:r['rss']); amps=np.asarray(two['complex_amplitudes_abs'],float)
    ratio=float(np.min(amps)/max(np.max(amps),1e-15)) if len(amps)==2 else 0.0
    beat_omega=float(abs(two['omegas'][0]-two['omegas'][1])); span=float(t[-1]-t[0]); beat_cycles=float(beat_omega*span/(2*np.pi))
    amp=np.abs(z); mod_depth=float(np.std(amp)/max(np.mean(amp),1e-15)); aa=amp-np.mean(amp)
    spec=np.abs(np.fft.rfft(aa*np.hanning(len(aa))))**2; ff=2*np.pi*np.fft.rfftfreq(len(aa),d=float(np.median(np.diff(t))))
    if len(spec)>1:
        j=1+int(np.argmax(spec[1:])); env_omega=float(ff[j]); env_rel=float(abs(env_omega-beat_omega)/max(abs(env_omega),abs(beat_omega),1e-15))
    else: env_omega=float('nan'); env_rel=float('inf')
    delta=float(one['bic']-two['bic'])
    support=bool(delta>=float(cfg['two_tone_delta_bic_min']) and two['nrmse']<=float(cfg['two_tone_nrmse_max']) and ratio>=float(cfg['two_tone_secondary_amplitude_ratio_min']) and beat_cycles>=float(cfg['two_tone_min_beat_cycles']) and mod_depth>=float(cfg['envelope_modulation_depth_min']) and env_rel<=float(cfg['envelope_beat_relative_error_max']))
    return {'status':'TWO_TONE_TEST_COMPLETE','support':support,'one_tone':one,'two_tone':two,'delta_bic_two_over_one':delta,'secondary_amplitude_ratio':ratio,'beat_angular_rate':beat_omega,'beat_cycles_over_horizon':beat_cycles,'envelope_modulation_depth':mod_depth,'envelope_dominant_angular_rate':env_omega,'envelope_beat_relative_error':env_rel,'angular_rate_units':'radian per dimensionless time unit'}


def instantaneous_rate_metrics(times, coeff, cfg):
    t=np.asarray(times,float); z=np.asarray(coeff,complex); amp=np.abs(z); phase=np.unwrap(np.angle(z))
    omega=_moving_average(np.gradient(phase,t),cfg['instantaneous_rate_smoothing_samples']); amp_s=_moving_average(amp,cfg['instantaneous_rate_smoothing_samples'])
    finite=np.isfinite(omega); scale=float(np.median(np.abs(omega[finite]))) if np.any(finite) else 0.0
    floor=max(float(cfg['instantaneous_rate_abs_floor']),float(cfg['instantaneous_rate_significance_fraction'])*scale)
    sig=np.where(np.abs(omega)>=floor)[0]; events=[]
    if len(sig)>1:
        prev=int(sig[0]); prev_sign=int(np.sign(omega[prev]))
        for ix0 in sig[1:]:
            ix=int(ix0); s=int(np.sign(omega[ix]))
            if s and prev_sign and s!=prev_sign:
                lo=min(prev,ix); hi=max(prev,ix); local=lo+int(np.argmin(np.abs(omega[lo:hi+1])))
                if not events or local-events[-1]>=int(cfg['minimum_reversal_separation_samples']): events.append(local)
                prev_sign=s
            prev=ix
    med_amp=float(np.median(amp_s)) if len(amp_s) else 0.0
    ratios=[float(amp_s[i]/max(med_amp,1e-15)) for i in events]
    low_frac=float(np.mean([r<=float(cfg['reversal_amplitude_ratio_max']) for r in ratios])) if ratios else 0.0
    reversal_support=bool(events and low_frac>=float(cfg['minimum_reversals_at_amplitude_dips_fraction']))
    x=(amp_s-np.mean(amp_s))/max(np.std(amp_s),1e-15); y=(omega-np.mean(omega))/max(np.std(omega),1e-15)
    best_corr=0.0; best_lag=0; maxlag=min(int(cfg['amplitude_rate_correlation_max_lag_samples']),max(0,len(x)//4))
    for lag in range(-maxlag,maxlag+1):
        if lag<0: a=x[-lag:]; b=y[:len(y)+lag]
        elif lag>0: a=x[:-lag]; b=y[lag:]
        else: a=x; b=y
        if len(a)<16: continue
        c=float(np.mean(a*b))
        if abs(c)>abs(best_corr): best_corr=c; best_lag=lag
    return {'status':'INSTANTANEOUS_RATE_TEST_COMPLETE','reversal_count':len(events),'reversal_indices':events,'significant_angular_rate_floor':floor,'reversal_amplitude_ratios':ratios,'reversal_amplitude_dip_fraction':low_frac,'reversal_amplitude_coupling_support':reversal_support,'amplitude_rate_max_abs_correlation':float(abs(best_corr)),'amplitude_rate_correlation_signed':float(best_corr),'amplitude_rate_correlation_lag_samples':int(best_lag),'amplitude_rate_coupling_support':bool(abs(best_corr)>=float(cfg['amplitude_rate_correlation_abs_min']))}


def phase_slip_metrics(times, coeff, reversal_indices, cfg):
    z=np.asarray(coeff,complex); amp=np.abs(z)
    if len(z)<16: return {'support':False,'status':'INSUFFICIENT_SAMPLES'}
    inc=np.angle(z[1:]*np.conj(z[:-1])); expected=_moving_average(inc,cfg['phase_slip_background_window_samples']); resid=_wrap(inc-expected)
    med=float(np.median(resid)); mad=float(np.median(np.abs(resid-med))); sigma=1.4826*mad
    threshold=max(float(cfg['phase_slip_absolute_jump_min']),float(cfg['phase_slip_mad_multiplier'])*sigma)
    raw=np.where(np.abs(resid-med)>=threshold)[0]; events=[]
    for ix0 in raw:
        ix=int(ix0)
        if not events or ix-events[-1]>=int(cfg['phase_slip_minimum_separation_samples']): events.append(ix)
        elif abs(resid[ix])>abs(resid[events[-1]]): events[-1]=ix
    med_amp=float(np.median(amp)); ratios=[float(min(amp[i],amp[min(i+1,len(amp)-1)])/max(med_amp,1e-15)) for i in events]
    low_frac=float(np.mean([r<=float(cfg['phase_slip_amplitude_ratio_max']) for r in ratios])) if ratios else 0.0
    tol=int(cfg['phase_slip_reversal_match_window_samples']); matched=sum(any(abs((e+1)-int(r))<=tol for e in events) for r in reversal_indices)
    match_frac=float(matched/len(reversal_indices)) if reversal_indices else 0.0
    support=bool(len(events)>=int(cfg['phase_slip_minimum_event_count']) and low_frac>=float(cfg['phase_slip_minimum_low_amplitude_fraction']) and (not reversal_indices or match_frac>=float(cfg['phase_slip_minimum_reversal_match_fraction'])))
    return {'status':'PHASE_SLIP_TEST_COMPLETE','support':support,'event_count':len(events),'event_indices':events,'jump_threshold_radians':threshold,'robust_sigma_radians':sigma,'event_amplitude_ratios':ratios,'low_amplitude_event_fraction':low_frac,'matched_reversal_fraction':match_frac}


def smooth_chirp_metrics(phase_metrics,cfg):
    p=phase_metrics or {}; q=p.get('quadratic_fit') or {}; rev=int(p.get('angular_rate_sign_reversal_count') or 0)
    support=bool(p.get('coherent',False) and rev<=int(cfg['smooth_chirp_max_sign_reversals']) and float(q.get('r2') or -np.inf)>=float(cfg['smooth_chirp_quadratic_r2_min']) and float(p.get('delta_bic_quadratic_over_linear') or -np.inf)>=float(cfg['smooth_chirp_delta_bic_min']) and float(q.get('nrmse') or np.inf)<=float(cfg['smooth_chirp_nrmse_max']) and float(p.get('quadratic_angular_rate_relative_change') or 0.0)>=float(cfg['smooth_chirp_relative_change_min']))
    return {'status':'SMOOTH_CHIRP_TEST_COMPLETE','support':support,'quadratic_r2':q.get('r2'),'delta_bic_quadratic_over_linear':p.get('delta_bic_quadratic_over_linear'),'quadratic_nrmse':q.get('nrmse'),'relative_angular_rate_change':p.get('quadratic_angular_rate_relative_change'),'sign_reversal_count':rev}


def quotient_recurrence_metrics(times, coeff_matrix, modes, selected_mode, cfg):
    t=np.asarray(times,float); C=np.asarray(coeff_matrix,complex); modes=np.asarray(modes,int)
    if selected_mode not in set(map(int,modes)) or len(C)<64: return {'rpo_candidate':False,'quotient_recurrence':False,'status':'INSUFFICIENT_STATE'}
    b=int(np.where(modes==int(selected_mode))[0][0]); m0=float(selected_mode)
    selected_phase=np.unwrap(np.angle(C[:,b])); theta=selected_phase/m0
    # Correct spatial/helical phase quotient: mode m transforms as exp(i*m*theta).
    Q=C*np.exp(-1j*theta[:,None]*modes[None,:])
    scale=np.sqrt(np.sum(np.abs(Q)**2,axis=1,keepdims=True)); Q=Q/np.maximum(scale,1e-15)
    state=np.concatenate([Q.real,Q.imag],axis=1); every=max(1,int(cfg['recurrence_sample_every']))
    state=state[::every]; theta=theta[::every]; tt=t[::every]
    center=np.mean(state,axis=0,keepdims=True); state=state-center
    rms=float(np.sqrt(np.mean(np.sum(state*state,axis=1))))
    if rms<=1e-14: return {'rpo_candidate':False,'quotient_recurrence':True,'status':'TRIVIAL_QUOTIENT_STATE'}
    n=len(state); minlag=max(1,int(np.ceil(float(cfg['recurrence_min_lag_steps'])/every))); maxlag=min((n-1)//2,max(minlag,int(np.floor(float(cfg['recurrence_max_lag_steps'])/every))))
    rows=[]
    for lag in range(minlag,maxlag+1,max(1,int(cfg['recurrence_lag_stride_samples']))):
        dist=np.sqrt(np.sum((state[lag:]-state[:-lag])**2,axis=1))/max(rms,1e-15); adv=theta[lag:]-theta[:-lag]
        conc=float(abs(np.mean(np.exp(1j*adv)))) if len(adv) else 0.0; mean_angle=float(np.angle(np.mean(np.exp(1j*adv)))) if len(adv) else float('nan')
        rows.append({'lag_samples':int(lag),'lag_steps':int(lag*every),'lag_time':float(tt[lag]-tt[0]),'median_quotient_distance':float(np.median(dist)),'q25_quotient_distance':float(np.quantile(dist,0.25)),'group_phase_advance_concentration':conc,'group_phase_advance_mean_angle':mean_angle,'pair_count':int(len(adv)),'estimated_repeat_count':int((n-1)//lag)})
    if not rows: return {'rpo_candidate':False,'quotient_recurrence':False,'status':'NO_VALID_LAGS'}
    best=min(rows,key=lambda r:(r['median_quotient_distance'],-r['group_phase_advance_concentration']))
    recur=bool(best['median_quotient_distance']<=float(cfg['recurrence_distance_max']) and best['pair_count']>=int(cfg['recurrence_min_pair_count']) and best['estimated_repeat_count']>=int(cfg['recurrence_min_repeat_count']))
    rpo=bool(recur and best['group_phase_advance_concentration']>=float(cfg['rpo_group_phase_advance_concentration_min']))
    return {'status':'RECURRENCE_TEST_COMPLETE','quotient_recurrence':recur,'rpo_candidate':rpo,'best':best,'lag_scan_count':len(rows),'quotient_action':'C_m -> C_m exp(-i*m*theta), theta=arg(C_selected)/m_selected','normalization':'unit modal L2 norm; centered quotient state'}


def mechanism_discrimination(times, selected_coeff, coeff_matrix, modes, selected_mode, phase_metrics, cfg):
    chirp=smooth_chirp_metrics(phase_metrics,cfg); tone=two_tone_metrics(times,selected_coeff,cfg); inst=instantaneous_rate_metrics(times,selected_coeff,cfg); slip=phase_slip_metrics(times,selected_coeff,inst.get('reversal_indices',[]),cfg); recur=quotient_recurrence_metrics(times,coeff_matrix,modes,selected_mode,cfg)
    beating=bool(tone.get('support',False))
    amp_mod=bool(inst.get('amplitude_rate_coupling_support',False) and not beating and not slip.get('support',False))
    flags={'smooth_chirp':bool(chirp.get('support',False)),'two_tone_beating':beating,'phase_slip':bool(slip.get('support',False)),'rpo_candidate':bool(recur.get('rpo_candidate',False)),'quotient_recurrence':bool(recur.get('quotient_recurrence',False)),'amplitude_phase_modulation':amp_mod}
    primary=[k for k in ('smooth_chirp','two_tone_beating','phase_slip','rpo_candidate','amplitude_phase_modulation') if flags[k]]
    if len(primary)>1: label='MIXED_MECHANISM_SIGNATURE'
    elif primary: label=primary[0].upper()+'_SIGNATURE'
    elif flags['quotient_recurrence']: label='QUOTIENT_RECURRENCE_WITHOUT_RPO_PHASE_CLOSURE'
    else: label='NONSTATIONARITY_MECHANISM_UNRESOLVED'
    return {'status':'MECHANISM_DISCRIMINATION_COMPLETE','label':label,'flags':flags,'smooth_chirp':chirp,'two_tone':tone,'instantaneous_rate':inst,'phase_slip':slip,'recurrence':recur}


def mechanism_metrics(frames, dt, persistence, kelvin_cfg, branch_cfg, mechanism_cfg):
    from .modes import transverse_mode_series
    from .nonstationary import branch_phase_metrics
    bp=branch_phase_metrics(frames,dt,persistence,kelvin_cfg,branch_cfg); modes,C=transverse_mode_series(frames,frames[0],kelvin_cfg['mode_min'],kelvin_cfg['mode_max']); selected=bp.get('selected_mode')
    if selected is None or selected not in set(map(int,modes)):
        mech={'status':'NO_SELECTED_MODE','label':'NONSTATIONARITY_MECHANISM_UNRESOLVED','flags':{k:False for k in ['smooth_chirp','two_tone_beating','phase_slip','rpo_candidate','quotient_recurrence','amplitude_phase_modulation']}}
    else:
        ix=int(np.where(modes==int(selected))[0][0]); times=np.arange(len(frames),dtype=float)*float(dt)
        mech=mechanism_discrimination(times,C[:,ix],C,modes,int(selected),bp.get('phase',{}),mechanism_cfg)
    return bp,mech
