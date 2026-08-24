from __future__ import annotations
import numpy as np
from .geometry import geometry_stats
from .eigen import convergence_mode,dispersion_branch
from .delay import loop_wavenumber,wavepacket_return
from .native import curve_basic_stats

TWOPI=2*np.pi


def _profile_metrics_from_conv(conv):
    rows=conv.get('levels',[]) if isinstance(conv,dict) else []
    for row in reversed(rows):
        pm=row.get('profile_metrics') if isinstance(row,dict) else None
        if isinstance(pm,dict): return pm
    return {}


def _clock_regime(clock,cfg):
    ratio=float(clock.get('mode_over_swirl_frequency_ratio',np.nan)); vg=abs(float(clock.get('group_velocity',np.nan)))
    if np.isfinite(ratio) and np.isfinite(vg):
        if float(cfg.get('fast_swirl_ratio_min',.60))<=ratio<=float(cfg.get('fast_swirl_ratio_max',1.40)) and vg>=float(cfg.get('fast_group_velocity_min',.05)):
            return 'FAST_SWIRL_LOCKED'
        if ratio<=float(cfg.get('slow_mode_ratio_max',.20)) and vg<=float(cfg.get('slow_group_velocity_max',.05)):
            return 'SLOW_MODE'
    return 'OTHER_BRANCH'


def _single_state(cand,cfg,Lhat,hol,slender_valid,offset,with_delay):
    khat=loop_wavenumber(Lhat,cand.m,cand.n,hol,float(offset))
    sel=dict(cfg.get('mode_selection',{}))
    conv=convergence_mode(cand.profile_name,cand.axial_ratio,cand.m,khat,cand.radial_levels,cand.rmax,sel)
    disp=dispersion_branch(cand.profile_name,cand.axial_ratio,cand.m,khat,cand.radial_n_dispersion,cand.rmax,float(cfg.get('dispersion_frac_step',.12)),int(cfg.get('dispersion_nside',3)),sel)
    mode_valid=bool(slender_valid and conv.get('converged',False) and disp.get('available',False))
    delay={'available':False,'reason':'not requested for symmetric control'}
    if with_delay and mode_valid:
        delay=wavepacket_return(
            Lhat,khat,float(disp['center_mode']['omega']),disp['poly_coeff'],float(disp['group_velocity']),
            int(cfg.get('wavepacket_modes',31)),int(cfg.get('wavepacket_times',401)),
            float(cfg.get('phase_step_max_rad',.05)),float(cfg.get('phase_uncertainty_max_rad',.35)),
            float(disp.get('omega_fit_rmse',np.nan)),float(cfg.get('return_coherence_min',.50)))
    delay_valid=bool(mode_valid and with_delay and delay.get('available',False))
    phase_valid=bool(delay_valid and delay.get('phase_valid',False))
    omega=float(conv.get('omega_median',np.nan)); lam_re=float(conv.get('growth_median',np.nan)); lam_im=-omega if np.isfinite(omega) else np.nan
    omega_intr=float(conv.get('omega_intrinsic_median',np.nan)); advf=float(conv.get('advective_frequency_median',np.nan))
    tmode=TWOPI/abs(lam_im) if np.isfinite(lam_im) and abs(lam_im)>1e-12 else np.nan
    tintr=TWOPI/abs(omega_intr) if np.isfinite(omega_intr) and abs(omega_intr)>1e-12 else np.nan
    pm=_profile_metrics_from_conv(conv); om_sw=float(pm.get('omega_swirl_rms_core',np.nan))
    vg=float(disp.get('group_velocity',np.nan)) if disp.get('available') else np.nan
    tau_group=float(delay.get('tau_group',np.nan)); tau_return=float(delay.get('tau_return',np.nan)); phase=float(delay.get('loop_phase',np.nan))
    clock={
        'lambda_real':lam_re,
        'lambda_imag':lam_im,
        'omega_mode':abs(lam_im) if np.isfinite(lam_im) else np.nan,
        'T_mode':tmode,
        'advective_frequency_mode_weighted':advf,
        'omega_intrinsic':omega_intr,
        'T_intrinsic':tintr,
        'group_velocity':vg,
        'tau_loop_group':tau_group,
        'tau_return_measured':tau_return,
        'phi_loop':phase,
        'phase_uncertainty_rad':float(delay.get('phase_uncertainty_rad',np.nan)),
        'phase_sampling_step_rad':float(delay.get('phase_sampling_step_rad',np.nan)),
        'dispersion_omega_rmse':float(delay.get('dispersion_omega_rmse',np.nan)),
        'carrier_phase_cycles_at_return':float(delay.get('carrier_phase_cycles_at_return',np.nan)),
        'omega_swirl_rms_core':om_sw,
        'mode_over_swirl_frequency_ratio':abs(lam_im)/max(abs(om_sw),1e-30) if np.isfinite(lam_im) and np.isfinite(om_sw) else np.nan,
        'intrinsic_over_swirl_frequency_ratio':abs(omega_intr)/max(abs(om_sw),1e-30) if np.isfinite(omega_intr) and np.isfinite(om_sw) else np.nan,
    }
    clock['clock_regime']=_clock_regime(clock,cfg)
    return {
        'closure_offset_evaluated':float(offset),'k_hat':float(khat),'eigen_convergence':_strip_vectors(conv),
        'dispersion':_strip_vectors(disp),'delay':delay,'mode_gate_valid':mode_valid,'delay_gate_valid':delay_valid,'phase_gate_valid':phase_valid,
        'growth_metric':float(conv.get('growth_positive_median',np.nan)),
        'signed_growth_median':lam_re,'omega_median':omega,'omega_intrinsic_median':omega_intr,'advective_frequency_median':advf,
        'hybridization_metric':float(conv.get('hybrid_median',np.nan)),
        'localization_metric':float(conv.get('localization_median',np.nan)),
        'loop_phase':phase,'tau_group':tau_group,'tau_return':tau_return,
        'tau_relative_error':float(delay.get('tau_relative_error',np.nan)),
        'return_coherence':float(delay.get('return_coherence',np.nan)),
        'phase_uncertainty_rad':float(delay.get('phase_uncertainty_rad',np.nan)),
        'clock_regime':clock['clock_regime'],'swirl_clock':clock,
    }


def analyze(cand,cfg):
    gs=geometry_stats(cand.components)
    native_L=sum(float(curve_basic_stats(c)['length']) for c in cand.components)
    native_len_err=abs(native_L-gs['length_total'])/max(gs['length_total'],1e-14)
    a=float(cand.core_fraction); L=float(gs['length_total']); Lhat=L/a; hol=float(gs['bishop_holonomy_mean'])
    slender=float(a*gs['curvature_max']); validity=slender<=float(cfg.get('max_core_curvature',.30))
    off=float(cand.closure_offset)
    common={
        'status':'OK','finite_core_model':'linearized incompressible Euler columnar core + slender closed-loop/Bishop holonomy',
        'delay_parameter_in_dynamics':False,'target_phase_in_dynamics':False,'geometry':gs,
        'native_geometry_length_relative_error':float(native_len_err),'core_fraction':a,'slender_core_parameter_max':slender,
        'slender_valid':validity,'profile_name_runtime':cand.profile_name,'axial_ratio_runtime':cand.axial_ratio,
        'm_runtime':cand.m,'n_runtime':cand.n,'closure_offset_runtime':off,'loop_length_over_core':Lhat,'bishop_holonomy':hol,
        'phase_measurement_semantics':'continuous envelope-peak refinement + dispersion/time uncertainty gate',
    }
    if abs(off)<=1e-14:
        st=_single_state(cand,cfg,Lhat,hol,validity,0.0,True)
        return {**common,'analysis_semantics':'EXACT_CLOSED_LOOP','eigenmode_gate_valid':bool(st['mode_gate_valid']),**st}

    # Symmetric +/- closure detuning around exact quantized k0.  It remains the
    # closure null in v0.1.2; only the Swirl-Clock phase measurement changed.
    d=abs(off); minus=_single_state(cand,cfg,Lhat,hol,validity,-d,False); plus=_single_state(cand,cfg,Lhat,hol,validity,+d,False)
    both=bool(minus['mode_gate_valid'] and plus['mode_gate_valid'])
    def avg(key):
        x=np.array([minus.get(key,np.nan),plus.get(key,np.nan)],float)
        return float(np.mean(x)) if np.all(np.isfinite(x)) else np.nan
    growth=avg('growth_metric'); signed=avg('signed_growth_median'); omega=avg('omega_median'); ointr=avg('omega_intrinsic_median'); advf=avg('advective_frequency_median'); hybrid=avg('hybridization_metric'); loc=avg('localization_metric')
    control={'minus':_strip_vectors(minus),'plus':_strip_vectors(plus),'delta_offset_abs':d,'delta_k_hat':float(TWOPI*d/max(Lhat,1e-30)),'first_order_k_slope_cancelled':True}
    return {
        **common,'analysis_semantics':'SYMMETRIC_PLUS_MINUS_K_CONTROL','symmetric_control':control,
        'eigenmode_gate_valid':both,'mode_gate_valid':both,'delay_gate_valid':False,'phase_gate_valid':False,
        'growth_metric':growth,'signed_growth_median':signed,'omega_median':omega,'omega_intrinsic_median':ointr,'advective_frequency_median':advf,
        'hybridization_metric':hybrid,'localization_metric':loc,
        'loop_phase':np.nan,'tau_group':np.nan,'tau_return':np.nan,'tau_relative_error':np.nan,'return_coherence':np.nan,'phase_uncertainty_rad':np.nan,
        'k_hat':float(loop_wavenumber(Lhat,cand.m,cand.n,hol,0.0)),'clock_regime':'CONTROL',
        'swirl_clock':{'lambda_real':signed,'lambda_imag':-omega if np.isfinite(omega) else np.nan,'omega_mode':abs(omega) if np.isfinite(omega) else np.nan,
                       'T_mode':TWOPI/abs(omega) if np.isfinite(omega) and abs(omega)>1e-12 else np.nan,'advective_frequency_mode_weighted':advf,
                       'omega_intrinsic':ointr,'T_intrinsic':TWOPI/abs(ointr) if np.isfinite(ointr) and abs(ointr)>1e-12 else np.nan,
                       'group_velocity':np.nan,'tau_loop_group':np.nan,'tau_return_measured':np.nan,'phi_loop':np.nan,'phase_uncertainty_rad':np.nan,
                       'phase_sampling_step_rad':np.nan,'dispersion_omega_rmse':np.nan,'carrier_phase_cycles_at_return':np.nan,
                       'omega_swirl_rms_core':np.nan,'mode_over_swirl_frequency_ratio':np.nan,'intrinsic_over_swirl_frequency_ratio':np.nan,'clock_regime':'CONTROL'},
    }


def _strip_vectors(x):
    if isinstance(x,dict):
        out={}
        for k,v in x.items():
            if k=='vector':continue
            out[k]=_strip_vectors(v)
        return out
    if isinstance(x,list):return [_strip_vectors(v) for v in x]
    if isinstance(x,complex):return {'real':float(x.real),'imag':float(x.imag)}
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,(np.floating,np.integer)):return x.item()
    return x
