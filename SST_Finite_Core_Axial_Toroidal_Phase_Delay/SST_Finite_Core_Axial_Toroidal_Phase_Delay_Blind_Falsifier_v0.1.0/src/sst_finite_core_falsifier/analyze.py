from __future__ import annotations
import numpy as np
from .geometry import geometry_stats
from .eigen import convergence_mode,dispersion_branch
from .delay import loop_wavenumber,wavepacket_return
from .native import curve_basic_stats

def analyze(cand,cfg):
    gs=geometry_stats(cand.components); native_L=sum(float(curve_basic_stats(c)['length']) for c in cand.components); native_len_err=abs(native_L-gs['length_total'])/max(gs['length_total'],1e-14); a=float(cand.core_fraction); L=float(gs['length_total']); Lhat=L/a; hol=float(gs['bishop_holonomy_mean']); slender=float(a*gs['curvature_max']); validity=slender<=float(cfg.get('max_core_curvature',.30))
    khat=loop_wavenumber(Lhat,cand.m,cand.n,hol,cand.closure_offset)
    sel=dict(cfg.get('mode_selection',{})); conv=convergence_mode(cand.profile_name,cand.axial_ratio,cand.m,khat,cand.radial_levels,cand.rmax,sel)
    disp=dispersion_branch(cand.profile_name,cand.axial_ratio,cand.m,khat,cand.radial_n_dispersion,cand.rmax,float(cfg.get('dispersion_frac_step',.12)),int(cfg.get('dispersion_nside',3)),sel)
    delay={'available':False,'reason':'dispersion unavailable'}
    if disp.get('available') and conv.get('n_good',0)>0:
        delay=wavepacket_return(Lhat,khat,float(disp['center_mode']['omega']),disp['poly_coeff'],float(disp['group_velocity']),int(cfg.get('wavepacket_modes',31)),int(cfg.get('wavepacket_times',401)))
    eig_ok=bool(validity and conv.get('converged',False) and disp.get('available',False) and delay.get('available',False))
    return {'status':'OK','finite_core_model':'linearized incompressible Euler columnar core + slender closed-loop/Bishop holonomy','delay_parameter_in_dynamics':False,'geometry':gs,'native_geometry_length_relative_error':float(native_len_err),'core_fraction':a,'slender_core_parameter_max':slender,'slender_valid':validity,'profile_name_runtime':cand.profile_name,'axial_ratio_runtime':cand.axial_ratio,'m_runtime':cand.m,'n_runtime':cand.n,'closure_offset_runtime':cand.closure_offset,'loop_length_over_core':Lhat,'bishop_holonomy':hol,'k_hat':khat,'eigen_convergence':_strip_vectors(conv),'dispersion':_strip_vectors(disp),'delay':delay,'eigenmode_gate_valid':eig_ok,'growth_metric':float(conv.get('growth_positive_median',np.nan)),'signed_growth_median':float(conv.get('growth_median',np.nan)),'hybridization_metric':float(conv.get('hybrid_median',np.nan)),'localization_metric':float(conv.get('localization_median',np.nan)),'loop_phase':float(delay.get('loop_phase',np.nan)),'tau_group':float(delay.get('tau_group',np.nan)),'tau_return':float(delay.get('tau_return',np.nan)),'tau_relative_error':float(delay.get('tau_relative_error',np.nan)),'return_coherence':float(delay.get('return_coherence',np.nan))}

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
