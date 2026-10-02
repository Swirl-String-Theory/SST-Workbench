from __future__ import annotations
import json, math, random, time
from pathlib import Path
import numpy as np
from native_ext.core import load_native, native_info, centerline_split, biot_savart, min_nonlocal_distance
from .io import load_curve, sha256_file
from .geometry import (arclength,resample_closed,detect_lobes,build_lobe_modes,shape_field,
                       apply_mode,nearest_cross_lobe_pair,distance_rate,circle,kabsch_align,normal_component,estimate_tube_thickness)
from .pressure import periodic_pressure_poisson
from .diagnostics import (modal_attribution,component_ablation,c3_block_diagnostics,closest_cross_lobe_pairs,
                          lobe_pair_centroid_rates,curvature_signature,signature_distance)
from .gate_catalog import GATE_CATALOG
from .coupled import coupled_analysis

DEFAULT_CONSTANTS = {
    'v_swirl_m_s': 1.09384563e6,
    'r_c_m': 1.40897017e-15,
    'rho_f_kg_m3': 7.0e-7,
}


def _jsonable(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,(np.floating,np.integer)): return x.item()
    if isinstance(x,complex): return {'re':float(x.real),'im':float(x.imag)}
    if isinstance(x,Path): return str(x)
    if isinstance(x,dict): return {str(k):_jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_jsonable(v) for v in x]
    return x


def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(_jsonable(data),indent=2,sort_keys=True),encoding='utf-8')


def rms(f): return float(np.sqrt(np.mean(np.sum(np.asarray(f,float)**2,axis=-1))))

def mode_project(modes,field): return np.array([float(np.mean(np.einsum('ij,ij->i',m,field))) for m in modes])

def eig_metrics(J):
    ev=np.linalg.eigvals(np.asarray(J,float)); scale=float(np.max(np.abs(ev))) if len(ev) else 0.0; mr=float(np.max(ev.real)) if len(ev) else 0.0
    return dict(eigenvalues=[{'re':float(z.real),'im':float(z.imag)} for z in ev],spectral_scale=scale,max_real=mr,normalized_growth=mr/max(scale,1e-12))


def split_shape_fields(x,split):
    return {k:shape_field(x,v)[0] for k,v in split.items()}


def resolve_core_radius(x,cfg):
    est=estimate_tube_thickness(x, stride=int(cfg.get('thickness_stride',2)), dcsc_tangent_tol=float(cfg.get('dcsc_tangent_tol',0.10)), min_separation_fraction=float(cfg.get('thickness_min_separation_fraction',0.08)), curvature_quantile=float(cfg.get('curvature_quantile',0.01)))
    mode=str(cfg.get('core_radius_mode','fixed_normalized'))
    if mode=='thickness_fraction': core=float(cfg.get('core_fraction_of_thickness',0.90))*est['thickness']
    elif mode=='fixed_normalized': core=float(cfg['core_radius_norm'])
    else: raise ValueError(f'unknown core_radius_mode={mode}')
    if not np.isfinite(core) or core<=0: raise ValueError(f'invalid resolved core radius {core}')
    return core,est


def base_metrics(x,labels,*,gamma,core,local_span,mod,cfg=None,deep_diagnostics=True):
    split,comp_backend=centerline_split(x,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
    sf=split_shape_fields(x,split); total_rms=rms(split['total']); shape_rms=rms(sf['total'])
    closure=split['local']+split['same_lobe']+split['cross_lobe']+split['transition']-split['total']
    skip=max(local_span+2,len(x)//12,6)
    pair=nearest_cross_lobe_pair(x,labels,skip=skip); i,j=pair['i'],pair['j']
    pair_rates={k:distance_rate(x,v,i,j) for k,v in split.items()} if i>=0 else {}
    mnd=min_nonlocal_distance(x,skip=skip,mod=mod)
    if deep_diagnostics:
        topk=int((cfg or {}).get('contact_top_k',12)); exclusion=int((cfg or {}).get('contact_pair_exclusion',max(2,len(x)//96)))
        contacts=closest_cross_lobe_pairs(x,labels,split,top_k=topk,skip=skip,exclusion=exclusion)
        lobe_pairs=lobe_pair_centroid_rates(x,labels,gamma=gamma,core=core)
    else:
        contacts={}; lobe_pairs={}
    return dict(
        component_backend=comp_backend,total_velocity_rms=total_rms,shape_velocity_rms=shape_rms,
        shape_velocity_ratio=shape_rms/max(total_rms,1e-30),component_shape_rms={k:rms(v) for k,v in sf.items()},
        split_closure_rel=rms(closure)/max(total_rms,1e-30),nearest_cross_lobe_pair=pair,
        nearest_pair_distance_rates=pair_rates,min_nonlocal_distance=mnd,
        contact_pair_diagnostics=contacts,lobe_pair_centroid_diagnostics=lobe_pairs,
    ),split,sf


def reduced_jacobian(x,mode_info,*,eps,gamma,core,local_span,mod):
    modes=mode_info['modes']; labels=mode_info['labels']; M=len(modes); keys=['total','local','same_lobe','cross_lobe','transition']
    J={k:np.zeros((M,M)) for k in keys}; pair_rows=[]
    for b,phi in enumerate(modes):
        xp=apply_mode(x,phi,+eps,target_length=2*np.pi); xm=apply_mode(x,phi,-eps,target_length=2*np.pi)
        sp,_=centerline_split(xp,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        sm,_=centerline_split(xm,labels,gamma=gamma,core=core,local_span=local_span,mod=mod)
        for k in keys:
            dv=(shape_field(xp,sp[k])[0]-shape_field(xm,sm[k])[0])/(2*eps)
            J[k][:,b]=mode_project(modes,dv)
        pp=nearest_cross_lobe_pair(x,labels,skip=max(local_span+2,len(x)//12,6)); i,j=pp['i'],pp['j']
        if i>=0:
            pair_rows.append(dict(mode=mode_info['names'][b],plus_total=distance_rate(xp,sp['total'],i,j),minus_total=distance_rate(xm,sm['total'],i,j),plus_cross=distance_rate(xp,sp['cross_lobe'],i,j),minus_cross=distance_rate(xm,sm['cross_lobe'],i,j)))
    metrics={k:eig_metrics(A) for k,A in J.items()}; metrics['without_cross']=eig_metrics(J['total']-J['cross_lobe'])
    diag={k:{mode_info['names'][i]:float(-J[k][i,i]) for i in range(M)} for k in keys}
    return dict(eps=float(eps),J=J,eigs=metrics,direct_restoring=diag,pair_perturbations=pair_rows)


def jacobian_convergence(jacs):
    if len(jacs)<2:return float('nan')
    mats=[np.asarray(j['J']['total']) for j in jacs]; refs=[]
    for a,b in zip(mats[:-1],mats[1:]): refs.append(float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-12)))
    return float(max(refs)) if refs else float('nan')


def make_scramble(x,mode_info,amp,phase):
    names=mode_info['names']; modes=mode_info['modes']; ids=[i for i,n in enumerate(names) if n.startswith('tilt_')]
    if len(ids)<3:return x.copy()
    f=np.cos(phase)*modes[ids[1]]+np.sin(phase)*modes[ids[2]]; f/=max(rms(f),1e-30)
    return apply_mode(x,f,amp,target_length=2*np.pi)


def control_metrics(x,*,cfg,gamma,core,mod,reference_signature=None):
    mi=build_lobe_modes(x); b,_,_=base_metrics(x,mi['labels'],gamma=gamma,core=core,local_span=cfg['local_span'],mod=mod,cfg=cfg,deep_diagnostics=False)
    j=reduced_jacobian(x,mi,eps=cfg['control_jacobian_eps'],gamma=gamma,core=core,local_span=cfg['local_span'],mod=mod)
    sig=curvature_signature(x)
    return dict(base=b,jacobian_summary={k:v for k,v in j['eigs'].items()},names=mi['names'],curvature_signature=sig,
                curvature_signature_distance=(signature_distance(reference_signature,sig) if reference_signature else float('nan')))


def ringdown(base,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    n=int(cfg.get('ringdown_n',0)); steps=int(cfg.get('ringdown_steps',0))
    if n<=0 or steps<=0:return None
    ref=resample_closed(base,n,target_length=2*np.pi); mi=build_lobe_modes(ref); names=mi['names']; idx=names.index('tilt_1') if 'tilt_1' in names else 0; phi=mi['modes'][idx]
    amp=float(cfg['ringdown_amp']); x=apply_mode(ref,phi,amp,target_length=2*np.pi); dtmax=float(cfg['ringdown_dt_max']); cfl=float(cfg['ringdown_cfl']); stride=max(1,int(cfg.get('ringdown_stride',10)))
    hist=[]; event=None; t=0.0; backend_used=None
    def vel_shape(y):
        nonlocal backend_used
        v,backend_used=biot_savart(y,y,gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
        return shape_field(y,v)[0]
    for step in range(steps+1):
        if step%stride==0 or step==steps:
            al=kabsch_align(ref,x); d=al-ref; q=float(np.mean(np.einsum('ij,ij->i',phi,d))); sr=rms(normal_component(ref,d)); md=min_nonlocal_distance(x,skip=max(cfg['local_span']+2,len(x)//12,6),mod=mod)
            hist.append(dict(step=step,t=t,mode_amplitude=q,shape_rms=sr,min_nonlocal_distance=md['distance']))
            if md['distance'] < float(cfg['core_event_factor'])*core:
                event=dict(step=step,t=t,distance=md['distance'],threshold=float(cfg['core_event_factor'])*core);break
        if step==steps:break
        v1=vel_shape(x); vmax=float(np.max(np.linalg.norm(v1,axis=1))); edge=float(np.mean(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))); dt=min(dtmax,cfl*edge/max(vmax,1e-12))
        mid=x+0.5*dt*v1; v2=vel_shape(mid); x=x+dt*v2; x=resample_closed(x,n,target_length=None,center=True); t+=dt
    initial=abs(hist[0]['mode_amplitude']) if hist else float('nan'); final=abs(hist[-1]['mode_amplitude']) if hist else float('nan'); mx=max(abs(h['mode_amplitude']) for h in hist) if hist else float('nan')
    return dict(mode=names[idx],backend=backend_used,history=hist,core_event=event,initial_abs_amplitude=initial,final_abs_amplitude=final,max_abs_amplitude=mx,final_over_initial=final/max(initial,1e-12),max_over_initial=mx/max(initial,1e-12))


def _dominant_real_mode_field(mode_info, modal_rows):
    row=modal_rows[0]
    z=np.asarray([complex(q['re'],q['im']) for q in row['right_coefficients']])
    a=z.real; b=z.imag; coeff=a if np.linalg.norm(a)>=np.linalg.norm(b) else b
    if np.linalg.norm(coeff)<1e-12: coeff=np.zeros(len(z)); coeff[0]=1.0
    f=np.tensordot(coeff,np.asarray(mode_info['modes']),axes=(0,0)); f/=max(rms(f),1e-30)
    return f,coeff.tolist()


def _early_log_growth(hist):
    if len(hist)<3:return float('nan')
    h=hist[:max(3,(len(hist)+1)//2)]; t=np.asarray([z['t'] for z in h],float); a=np.asarray([z['modal_norm'] for z in h],float)
    if np.ptp(t)<=0:return float('nan')
    y=np.log(np.maximum(a,1e-12)); return float(np.polyfit(t,y,1)[0])


def counterfactual_ringdown(base,modal_rows,*,cfg,gamma,core,mod):
    n=int(cfg.get('counterfactual_n',0)); steps=int(cfg.get('counterfactual_steps',0))
    if n<=0 or steps<=0 or not modal_rows:return None
    ref=resample_closed(base,n,target_length=2*np.pi); mi=build_lobe_modes(ref); labels=mi['labels']; phi,coeff=_dominant_real_mode_field(mi,modal_rows)
    amp=float(cfg.get('counterfactual_amp',0.006)); dtmax=float(cfg.get('counterfactual_dt_max',0.0004)); cfl=float(cfg.get('counterfactual_cfl',0.1)); stride=max(1,int(cfg.get('counterfactual_stride',4)))
    x0=apply_mode(ref,phi,amp,target_length=2*np.pi)
    variants=('full','without_cross')
    outs={}
    for variant in variants:
        x=x0.copy(); hist=[]; t=0.0; event=None
        def velocity(y):
            sp,_=centerline_split(y,labels,gamma=gamma,core=core,local_span=cfg['local_span'],mod=mod)
            raw=sp['total'] if variant=='full' else sp['total']-sp['cross_lobe']
            return shape_field(y,raw)[0]
        for step in range(steps+1):
            if step%stride==0 or step==steps:
                al=kabsch_align(ref,x); d=normal_component(ref,al-ref); q=mode_project(mi['modes'],d); mn=float(np.linalg.norm(q)); md=min_nonlocal_distance(x,skip=max(cfg['local_span']+2,len(x)//12,6),mod=mod)
                hist.append(dict(step=step,t=t,modal_norm=mn,mode_projection=q.tolist(),min_nonlocal_distance=md['distance']))
                if md['distance']<float(cfg['core_event_factor'])*core:
                    event=dict(step=step,t=t,distance=md['distance'],threshold=float(cfg['core_event_factor'])*core);break
            if step==steps:break
            v1=velocity(x); vmax=float(np.max(np.linalg.norm(v1,axis=1))); edge=float(np.mean(np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1))); dt=min(dtmax,cfl*edge/max(vmax,1e-12))
            mid=x+0.5*dt*v1; v2=velocity(mid); x=resample_closed(x+dt*v2,n,target_length=None,center=True); t+=dt
        outs[variant]=dict(history=hist,early_log_growth=_early_log_growth(hist),core_event=event,
                           final_over_initial=(hist[-1]['modal_norm']/max(hist[0]['modal_norm'],1e-12) if hist else float('nan')))
    return dict(dominant_mode_coefficients=coeff,dominant_linear_eigenvalue=modal_rows[0]['eigenvalue'],variants=outs)


def pressure_metrics(base,mode_info,*,cfg,gamma,core,backend,allow_sycl_cpu,mod):
    N=int(cfg.get('pressure_grid_n',0))
    if N<=0:return None
    p=periodic_pressure_poisson(base,core=core,gamma=gamma,grid_n=N,padding=float(cfg.get('pressure_padding',1.0)),backend=backend,mod=mod,allow_sycl_cpu=allow_sycl_cpu)
    acc=shape_field(base,p.pop('pressure_accel'))[0]; p['mode_projection']=dict(zip(mode_info['names'],mode_project(mode_info['modes'],acc).tolist()));p['accel_shape_rms']=rms(acc);return p


def dataset_analysis(blind_id,curve,*,cfg,backend,allow_sycl_cpu,mod):
    x=resample_closed(curve,int(cfg['n_points']),target_length=2*np.pi); peaks,labels,_=detect_lobes(x); mi=build_lobe_modes(x,peaks,labels)
    core,thickness=resolve_core_radius(x,cfg)
    base,split,sf=base_metrics(x,labels,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod,cfg=cfg)
    jacs=[reduced_jacobian(x,mi,eps=e,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod) for e in cfg['eps_values']]
    conv=jacobian_convergence(jacs); mid=jacs[len(jacs)//2]
    modal=modal_attribution(mid['J'],mi['names']); ablation=component_ablation(mid['J']); c3=c3_block_diagnostics(mid['J']['total'],mi['names'])
    refsig=curvature_signature(x); controls=[]; rng=np.random.default_rng(int(cfg['blind_seed'])+sum(map(ord,blind_id)))
    for k in range(int(cfg['n_scrambled_controls'])):
        phase=float(rng.uniform(0,2*np.pi)); xc=make_scramble(x,mi,float(cfg['scramble_amp']),phase); cm=control_metrics(xc,cfg=cfg,gamma=1.0,core=core,mod=mod,reference_signature=refsig);cm['phase']=phase;controls.append(cm)
    rd=ringdown(x,cfg=cfg,gamma=1.0,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    cf=counterfactual_ringdown(x,modal,cfg=cfg,gamma=1.0,core=core,mod=mod)
    pm=pressure_metrics(x,mi,cfg=cfg,gamma=1.0,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    coupled=None
    if bool(cfg.get('enable_coupled_tbk',True)):
        coupled=coupled_analysis(x,cfg=cfg,gamma=1.0,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    return dict(blind_id=blind_id,n_points=len(x),arclength=arclength(x),core_radius_norm=core,thickness_estimate=thickness,lobe_peaks=peaks.tolist(),mode_names=mi['names'],
                base=base,jacobians=jacs,jacobian_convergence=conv,modal_attribution=modal,component_ablation=ablation,c3_diagnostics=c3,
                reference_curvature_signature=refsig,controls=controls,ringdown=rd,counterfactual_ringdown=cf,pressure_poisson=pm,coupled_tbk=coupled,
                geometry=x,modes=mi['modes'],labels=labels)


def _gate_detail(gid,passed,measurements,criterion):
    meta=GATE_CATALOG[gid]
    return dict(passed=bool(passed),role=meta['role'],title=meta['title'],question=meta['question'],measurements=measurements,criterion=criterion,
                conclusion=(meta['pass_text'] if passed else meta['fail_text']))


def score_dataset(res,cfg):
    base=res['base']; j=res['jacobians'][len(res['jacobians'])//2]; et=j['eigs']['total']; ew=j['eigs']['without_cross']; cross=j['J']['cross_lobe']; total=j['J']['total']; names=res['mode_names']; tilt=[i for i,n in enumerate(names) if n.startswith('tilt_')]
    cross_pair=float(base['nearest_pair_distance_rates'].get('cross_lobe',float('nan')))
    cross_frac=float(np.linalg.norm(cross)/max(np.linalg.norm(total),1e-12)); improvement=float(ew['max_real']-et['max_real'])/max(et['spectral_scale'],ew['spectral_scale'],1e-12)
    direct_cross=[float(-cross[i,i]) for i in tilt]; direct_total=[float(-total[i,i]) for i in tilt]
    ctrl_growth=[c['jacobian_summary']['total']['normalized_growth'] for c in res['controls']]
    ctrl_specificity=(float(np.median(ctrl_growth))-et['normalized_growth']) if ctrl_growth else float('nan')
    match_tol=float(cfg.get('matched_control_curvature_distance_max',0.08)); matched=[c for c in res['controls'] if c['curvature_signature_distance']<=match_tol]
    matched_growth=[c['jacobian_summary']['total']['normalized_growth'] for c in matched]
    matched_delta=(float(np.median(matched_growth))-et['normalized_growth']) if matched_growth else float('nan')
    core=float(res['core_radius_norm']); thickness=float(res['thickness_estimate']['thickness']); core_clear=thickness/core
    contacts=base['contact_pair_diagnostics']; lobep=base['lobe_pair_centroid_diagnostics']
    rep_frac=float(contacts['positive_fraction']); rep_med=float(contacts['median_cross_rate']); lobe_frac=float(lobep['positive_fraction'])
    dominant=res['modal_attribution'][0]; cross_dom=float(dominant['contributions']['cross_lobe']['re']); cross_dom_norm=cross_dom/max(et['spectral_scale'],1e-12)
    parts=dominant['sector_participation']; sector_peak=max(float(parts['m0']),float(parts['E_tilt']),float(parts['E_breathe'])); c3_leak=float(res['c3_diagnostics']['block_leakage'])
    cf=res.get('counterfactual_ringdown'); cf_obs=float('nan'); cf_consistent=False; fg=float('nan'); ng=float('nan')
    if cf:
        fg=float(cf['variants']['full']['early_log_growth']); ng=float(cf['variants']['without_cross']['early_log_growth']); cf_obs=fg-ng
        minobs=float(cfg.get('counterfactual_growth_difference_min',1e-4))
        cf_consistent=bool(np.isfinite(cf_obs) and abs(cf_obs)>=minobs and cross_dom*cf_obs>0)
    gates={
      'G0_numerical_sanity': bool(base['split_closure_rel']<=cfg['split_closure_max'] and core_clear>=cfg['min_thickness_over_core']),
      'G1_relative_equilibrium': bool(base['shape_velocity_ratio']<=cfg['base_shape_ratio_max']),
      'G2_reduced_stability': bool(et['normalized_growth']<=cfg['normalized_growth_max'] and res['jacobian_convergence']<=cfg['jacobian_convergence_max']),
      'G3_cross_lobe_stabilizes': bool(cross_frac>=cfg['cross_jacobian_fraction_min'] and improvement>=cfg['cross_growth_improvement_min']),
      'G4_nearest_pair_cross_separates': bool(np.isfinite(cross_pair) and cross_pair>cfg['cross_pair_rate_min']),
      'G5_orientation_specificity': bool(np.isfinite(ctrl_specificity) and ctrl_specificity>=cfg['control_growth_delta_min']),
      'G6_ringdown_bounded': bool(res['ringdown'] is not None and res['ringdown']['core_event'] is None and res['ringdown']['max_over_initial']<=cfg['ringdown_max_over_initial']),
      'G7_matched_orientation_specificity': bool(len(matched)>=int(cfg.get('matched_control_min_count',2)) and np.isfinite(matched_delta) and matched_delta>=cfg.get('matched_control_growth_delta_min',cfg['control_growth_delta_min'])),
      'G8_cross_repulsion_coherent': bool(rep_frac>=cfg.get('contact_repulsion_fraction_min',0.6) and rep_med>cfg.get('contact_repulsion_median_min',0.0) and lobe_frac>=cfg.get('lobe_pair_repulsion_fraction_min',2/3)),
      'G9_dominant_mode_cross_stabilizes': bool(cross_dom_norm<=-abs(float(cfg.get('dominant_cross_stabilization_min',0.02)))),
      'G10_C3_sector_localized': bool(sector_peak>=cfg.get('c3_sector_participation_min',0.65) and c3_leak<=cfg.get('c3_block_leakage_max',0.35)),
      'G11_counterfactual_causal_consistency': bool(cf_consistent),
    }
    details={}
    details['G0_numerical_sanity']=_gate_detail('G0_numerical_sanity',gates['G0_numerical_sanity'],{'split_closure_rel':base['split_closure_rel'],'core_clearance_radii':core_clear},{'split_closure_max':cfg['split_closure_max'],'min_thickness_over_core':cfg['min_thickness_over_core']})
    details['G1_relative_equilibrium']=_gate_detail('G1_relative_equilibrium',gates['G1_relative_equilibrium'],{'shape_velocity_ratio':base['shape_velocity_ratio']},{'base_shape_ratio_max':cfg['base_shape_ratio_max']})
    details['G2_reduced_stability']=_gate_detail('G2_reduced_stability',gates['G2_reduced_stability'],{'normalized_growth':et['normalized_growth'],'jacobian_convergence':res['jacobian_convergence']},{'normalized_growth_max':cfg['normalized_growth_max'],'jacobian_convergence_max':cfg['jacobian_convergence_max']})
    details['G3_cross_lobe_stabilizes']=_gate_detail('G3_cross_lobe_stabilizes',gates['G3_cross_lobe_stabilizes'],{'cross_jacobian_fraction':cross_frac,'cross_growth_improvement':improvement},{'cross_jacobian_fraction_min':cfg['cross_jacobian_fraction_min'],'cross_growth_improvement_min':cfg['cross_growth_improvement_min']})
    details['G4_nearest_pair_cross_separates']=_gate_detail('G4_nearest_pair_cross_separates',gates['G4_nearest_pair_cross_separates'],{'nearest_pair_cross_rate':cross_pair},{'cross_pair_rate_min':cfg['cross_pair_rate_min']})
    details['G5_orientation_specificity']=_gate_detail('G5_orientation_specificity',gates['G5_orientation_specificity'],{'control_growth_delta':ctrl_specificity,'control_count':len(ctrl_growth)},{'control_growth_delta_min':cfg['control_growth_delta_min']})
    details['G6_ringdown_bounded']=_gate_detail('G6_ringdown_bounded',gates['G6_ringdown_bounded'],{'max_over_initial':(res['ringdown']['max_over_initial'] if res['ringdown'] else None),'core_event':(res['ringdown']['core_event'] if res['ringdown'] else None)},{'ringdown_max_over_initial':cfg['ringdown_max_over_initial'],'core_event_required_absent':True})
    details['G7_matched_orientation_specificity']=_gate_detail('G7_matched_orientation_specificity',gates['G7_matched_orientation_specificity'],{'matched_control_count':len(matched),'matched_control_growth_delta':matched_delta,'curvature_match_tolerance':match_tol},{'matched_control_min_count':cfg.get('matched_control_min_count',2),'matched_control_growth_delta_min':cfg.get('matched_control_growth_delta_min',cfg['control_growth_delta_min'])})
    details['G8_cross_repulsion_coherent']=_gate_detail('G8_cross_repulsion_coherent',gates['G8_cross_repulsion_coherent'],{'contact_positive_fraction':rep_frac,'contact_median_cross_rate':rep_med,'lobe_pair_positive_fraction':lobe_frac,'angle_rate_correlation':contacts['antiparallelness_rate_correlation']},{'contact_repulsion_fraction_min':cfg.get('contact_repulsion_fraction_min',0.6),'contact_repulsion_median_min':cfg.get('contact_repulsion_median_min',0.0),'lobe_pair_repulsion_fraction_min':cfg.get('lobe_pair_repulsion_fraction_min',2/3)})
    details['G9_dominant_mode_cross_stabilizes']=_gate_detail('G9_dominant_mode_cross_stabilizes',gates['G9_dominant_mode_cross_stabilizes'],{'dominant_eigenvalue':dominant['eigenvalue'],'cross_real_contribution':cross_dom,'cross_real_normalized':cross_dom_norm,'all_component_contributions':dominant['contributions']},{'cross_real_normalized_max':-abs(float(cfg.get('dominant_cross_stabilization_min',0.02)))})
    details['G10_C3_sector_localized']=_gate_detail('G10_C3_sector_localized',gates['G10_C3_sector_localized'],{'dominant_sector':dominant['dominant_sector'],'sector_participation':parts,'sector_peak':sector_peak,'block_leakage':c3_leak},{'c3_sector_participation_min':cfg.get('c3_sector_participation_min',0.65),'c3_block_leakage_max':cfg.get('c3_block_leakage_max',0.35)})
    details['G11_counterfactual_causal_consistency']=_gate_detail('G11_counterfactual_causal_consistency',gates['G11_counterfactual_causal_consistency'],{'linear_cross_real_contribution':cross_dom,'full_early_log_growth':fg,'without_cross_early_log_growth':ng,'nonlinear_full_minus_without_cross_growth':cf_obs,'full_core_event':(cf['variants']['full']['core_event'] if cf else None),'without_cross_core_event':(cf['variants']['without_cross']['core_event'] if cf else None)},{'same_sign_required':True,'minimum_absolute_growth_difference':cfg.get('counterfactual_growth_difference_min',1e-4)})

    # v0.3 diagnostics: coupled torsion/breathing/Kelvin balance, RPO recurrence and finite-difference Floquet return map.
    cp=res.get('coupled_tbk') or {}
    cs=(cp.get('spectrum') or [{}])[0] if cp.get('spectrum') else {}
    # Use the selected oscillatory mode for family participation if available; otherwise dominant growth mode.
    sel=(cp.get('rpo') or {}).get('selected_mode') or cs
    part=sel.get('family_participation',{}) if sel else {}
    fam_min=min(float(part.get('breathing',0.0)),float(part.get('torsion',0.0)),float(part.get('kelvin',0.0))) if part else 0.0
    abl=cp.get('family_coupling_ablation',{})
    tors_pen=float(abl.get('decouple_torsion',{}).get('growth_penalty_vs_full',float('nan')))
    kelv_pen=float(abl.get('decouple_kelvin',{}).get('growth_penalty_vs_full',float('nan')))
    brea_pen=float(abl.get('decouple_breathing',{}).get('growth_penalty_vs_full',float('nan')))
    all_pen=float(abl.get('block_diagonal_families',{}).get('growth_penalty_vs_full',float('nan')))
    pl=cp.get('phase_lock') or {}; rpo=(cp.get('rpo') or {}).get('candidate'); floq=cp.get('floquet') or {}
    rec=float(rpo.get('best_recurrence',float('nan'))) if rpo else float('nan')
    lock=float(pl.get('phase_lock_strength',float('nan'))) if pl.get('valid') else float('nan')
    fspread=float(pl.get('relative_frequency_spread',float('nan'))) if pl.get('valid') else float('nan')
    rho=float(floq.get('spectral_radius_excluding_neutral',float('nan'))) if floq.get('valid') else float('nan')
    cconv=float(cp.get('jacobian_convergence',float('nan')))
    gates.update({
      'G12_TBK_mode_resolved': bool(part and fam_min>=cfg.get('coupled_family_participation_min',0.02) and np.isfinite(cconv) and cconv<=cfg.get('coupled_jacobian_convergence_max',0.30)),
      'G13_torsion_coupling_stabilizes': bool(np.isfinite(tors_pen) and tors_pen>=cfg.get('family_coupling_stabilization_min',0.01)),
      'G14_kelvin_coupling_stabilizes': bool(np.isfinite(kelv_pen) and kelv_pen>=cfg.get('family_coupling_stabilization_min',0.01)),
      'G15_breathing_coupling_stabilizes': bool(np.isfinite(brea_pen) and brea_pen>=cfg.get('family_coupling_stabilization_min',0.01)),
      'G16_TBK_collective_coupling_stabilizes': bool(np.isfinite(all_pen) and all_pen>=cfg.get('collective_coupling_stabilization_min',0.02)),
      'G17_TBK_phase_lock': bool(pl.get('valid') and lock>=cfg.get('phase_lock_strength_min',0.65) and fspread<=cfg.get('phase_frequency_spread_max',0.25)),
      'G18_RPO_recurrence': bool(rpo is not None and rpo.get('excursion_reached',False) and np.isfinite(rec) and rec<=cfg.get('rpo_recurrence_max',0.05) and float(rpo.get('return_ratio',float('inf')))<=cfg.get('rpo_return_ratio_max',0.65) and rpo.get('core_event') is None),
      'G19_Floquet_bounded': bool(floq.get('valid') and np.isfinite(rho) and rho<=cfg.get('floquet_spectral_radius_max',1.05)),
    })
    details['G12_TBK_mode_resolved']=_gate_detail('G12_TBK_mode_resolved',gates['G12_TBK_mode_resolved'],{'selected_eigenvalue':sel.get('eigenvalue') if sel else None,'family_participation':part,'minimum_TBK_participation':fam_min,'coupled_jacobian_convergence':cconv},{'coupled_family_participation_min':cfg.get('coupled_family_participation_min',0.02),'coupled_jacobian_convergence_max':cfg.get('coupled_jacobian_convergence_max',0.30)})
    details['G13_torsion_coupling_stabilizes']=_gate_detail('G13_torsion_coupling_stabilizes',gates['G13_torsion_coupling_stabilizes'],{'growth_penalty_when_torsion_decoupled':tors_pen},{'family_coupling_stabilization_min':cfg.get('family_coupling_stabilization_min',0.01)})
    details['G14_kelvin_coupling_stabilizes']=_gate_detail('G14_kelvin_coupling_stabilizes',gates['G14_kelvin_coupling_stabilizes'],{'growth_penalty_when_kelvin_decoupled':kelv_pen},{'family_coupling_stabilization_min':cfg.get('family_coupling_stabilization_min',0.01)})
    details['G15_breathing_coupling_stabilizes']=_gate_detail('G15_breathing_coupling_stabilizes',gates['G15_breathing_coupling_stabilizes'],{'growth_penalty_when_breathing_decoupled':brea_pen},{'family_coupling_stabilization_min':cfg.get('family_coupling_stabilization_min',0.01)})
    details['G16_TBK_collective_coupling_stabilizes']=_gate_detail('G16_TBK_collective_coupling_stabilizes',gates['G16_TBK_collective_coupling_stabilizes'],{'growth_penalty_when_all_families_block_diagonalized':all_pen},{'collective_coupling_stabilization_min':cfg.get('collective_coupling_stabilization_min',0.02)})
    details['G17_TBK_phase_lock']=_gate_detail('G17_TBK_phase_lock',gates['G17_TBK_phase_lock'],{'phase_lock_valid':pl.get('valid',False),'phase_lock_strength':lock,'relative_frequency_spread':fspread,'pair_phase_locks':pl.get('pairs')},{'phase_lock_strength_min':cfg.get('phase_lock_strength_min',0.65),'phase_frequency_spread_max':cfg.get('phase_frequency_spread_max',0.25)})
    details['G18_RPO_recurrence']=_gate_detail('G18_RPO_recurrence',gates['G18_RPO_recurrence'],{'excursion_reached':(rpo.get('excursion_reached') if rpo else False),'peak_before_return':(rpo.get('peak_before_return') if rpo else None),'return_ratio':(rpo.get('return_ratio') if rpo else None),'best_recurrence':rec,'best_period_steps':(rpo.get('best_step') if rpo else None),'best_period_time':(rpo.get('best_time') if rpo else None),'core_event':(rpo.get('core_event') if rpo else None)},{'rpo_excursion_min':cfg.get('rpo_excursion_min',0.012),'rpo_recurrence_max':cfg.get('rpo_recurrence_max',0.05),'rpo_return_ratio_max':cfg.get('rpo_return_ratio_max',0.65),'core_event_required_absent':True})
    details['G19_Floquet_bounded']=_gate_detail('G19_Floquet_bounded',gates['G19_Floquet_bounded'],{'floquet_valid':floq.get('valid',False),'reason':floq.get('reason'),'spectral_radius_excluding_neutral':rho,'period_steps':floq.get('period_steps'),'period_time':floq.get('period_time')},{'floquet_requires_RPO_recurrence':True,'floquet_spectral_radius_max':cfg.get('floquet_spectral_radius_max',1.05)})
    critical=['G0_numerical_sanity','G2_reduced_stability','G3_cross_lobe_stabilizes','G4_nearest_pair_cross_separates','G6_ringdown_bounded']
    status='PASS' if all(gates[k] for k in critical) else 'FAIL'
    if (not gates['G0_numerical_sanity']) or res['jacobian_convergence']>2*cfg['jacobian_convergence_max']: status='INCONCLUSIVE'
    metrics=dict(core_clearance_radii=core_clear,shape_velocity_ratio=base['shape_velocity_ratio'],normalized_growth=et['normalized_growth'],cross_jacobian_fraction=cross_frac,cross_growth_improvement=improvement,nearest_pair_cross_rate=cross_pair,direct_cross_restoring_tilt=direct_cross,direct_total_restoring_tilt=direct_total,control_growth_delta=ctrl_specificity,jacobian_convergence=res['jacobian_convergence'],matched_control_growth_delta=matched_delta,matched_control_count=len(matched),contact_cross_positive_fraction=rep_frac,contact_cross_median_rate=rep_med,lobe_pair_positive_fraction=lobe_frac,dominant_cross_real_contribution=cross_dom,dominant_cross_real_normalized=cross_dom_norm,c3_sector_peak=sector_peak,c3_block_leakage=c3_leak,counterfactual_growth_difference=cf_obs,TBK_min_family_participation=fam_min,TBK_jacobian_convergence=cconv,torsion_decouple_growth_penalty=tors_pen,kelvin_decouple_growth_penalty=kelv_pen,breathing_decouple_growth_penalty=brea_pen,TBK_block_diagonal_growth_penalty=all_pen,phase_lock_strength=lock,phase_frequency_spread=fspread,rpo_best_recurrence=rec,floquet_spectral_radius_excluding_neutral=rho)
    return dict(status=status,gates=gates,gate_details=details,critical_gates=critical,metrics=metrics)


def circle_null(cfg,mod,core):
    x=circle(int(cfg['n_points'])); labels=np.zeros(len(x),np.int32); split,_=centerline_split(x,labels,gamma=1.0,core=core,local_span=cfg['local_span'],mod=mod); v=split['total']; radial=x.copy();radial[:,2]=0;radial/=np.linalg.norm(radial,axis=1)[:,None]; radial_rate=float(np.mean(np.einsum('ij,ij->i',v,radial))); sf=shape_field(x,v)[0]
    return dict(radial_velocity_mean=radial_rate,total_velocity_rms=rms(v),shape_velocity_rms=rms(sf),shape_velocity_ratio=rms(sf)/max(rms(v),1e-30),pass_null=bool(abs(radial_rate)<=cfg['circle_radial_rate_max']))


def physical_scales(cfg,a):
    c={**DEFAULT_CONSTANTS,**cfg.get('constants',{})}; a=float(a); rc=c['r_c_m']; vs=c['v_swirl_m_s']; Gamma=2*np.pi*rc*vs; ell=rc/a; t0=ell*ell/Gamma; v0=Gamma/ell; p0=c['rho_f_kg_m3']*v0*v0
    return dict(Gamma_SST_m2_s=Gamma,length_scale_m=ell,time_scale_s=t0,velocity_scale_m_s=v0,pressure_scale_Pa=p0,normalized_core=a,physical_core_m=rc,normalized_total_length=2*np.pi,physical_total_length_m=2*np.pi*ell)


def run_campaign(*,fseries_path,knotplot_path,config,out_dir,backend='auto',allow_sycl_cpu=False,force_build=False,build_verbose=False):
    cfg=json.loads(Path(config).read_text(encoding='utf-8')) if isinstance(config,(str,Path)) else dict(config); out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    write_json(out/'00_preregistered_config.json',cfg); inputs=[('fremlin_fseries','fseries',Path(fseries_path)),('knotplot_final','knotplot',Path(knotplot_path))]
    for _,_,p in inputs:
        if not p.exists(): raise FileNotFoundError(p)
    manifest=[dict(source=s,kind=k,path=str(p),sha256=sha256_file(p)) for s,k,p in inputs]
    rng=random.Random(int(cfg['blind_seed'])); order=list(range(len(inputs)));rng.shuffle(order); blind={order[i]:f'B{i+1:02d}' for i in range(len(order))}
    write_json(out/'blind_input_hashes.json',[{'blind_id':blind[i],'sha256':manifest[i]['sha256']} for i in range(len(inputs))])
    mod=load_native(force_build=force_build,build_verbose=build_verbose); info=native_info(mod); write_json(out/'backend_info.json',info)
    curves={}
    for idx,(source,kind,p) in enumerate(inputs): curves[blind[idx]]=load_curve(p,kind,n_raw=int(cfg.get('fseries_raw_samples',4096)))
    pre=out/'pre_unblind';pre.mkdir(exist_ok=True); results={};scores={}; t0=time.time()
    for bid in sorted(curves):
        r=dataset_analysis(bid,curves[bid],cfg=cfg,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod);results[bid]=r;scores[bid]=score_dataset(r,cfg)
        compact={k:v for k,v in r.items() if k not in ('geometry','modes','labels')}
        if compact.get('coupled_tbk'):
            compact['coupled_tbk']=dict(compact['coupled_tbk'])
            compact['coupled_tbk'].pop('geometry',None); compact['coupled_tbk'].pop('modes',None); compact['coupled_tbk'].pop('jacobian_total',None); compact['coupled_tbk'].pop('jacobian_cross',None)
            if compact['coupled_tbk'].get('rpo') and compact['coupled_tbk']['rpo'].get('candidate'):
                compact['coupled_tbk']['rpo']=dict(compact['coupled_tbk']['rpo']); compact['coupled_tbk']['rpo']['candidate']=dict(compact['coupled_tbk']['rpo']['candidate'])
                compact['coupled_tbk']['rpo']['candidate'].pop('initial_geometry',None); compact['coupled_tbk']['rpo']['candidate'].pop('final_geometry',None)
        write_json(pre/f'{bid}_analysis.json',compact);write_json(pre/f'{bid}_score.json',scores[bid])
        arrays=dict(geometry=r['geometry'],modes=r['modes'],labels=r['labels'],**{f'J_total_eps{i}':j['J']['total'] for i,j in enumerate(r['jacobians'])},**{f'J_cross_eps{i}':j['J']['cross_lobe'] for i,j in enumerate(r['jacobians'])})
        if r.get('coupled_tbk'):
            arrays.update(coupled_geometry=r['coupled_tbk']['geometry'],coupled_modes=r['coupled_tbk']['modes'],coupled_J_total=r['coupled_tbk']['jacobian_total'],coupled_J_cross=r['coupled_tbk']['jacobian_cross'])
            fl=r['coupled_tbk'].get('floquet') or {}
            if fl.get('valid'): arrays['floquet_monodromy']=np.asarray(fl['monodromy'])
        np.savez_compressed(pre/f'{bid}_arrays.npz',**arrays)
    nulls={b:circle_null(cfg,mod,results[b]['core_radius_norm']) for b in sorted(results)};write_json(pre/'circle_nulls.json',nulls)
    critical_status=[scores[b]['status'] for b in sorted(scores)]; null_ok=all(z['pass_null'] for z in nulls.values())
    if all(s=='PASS' for s in critical_status) and null_ok: overall='PASS'
    elif any(s=='INCONCLUSIVE' for s in critical_status) or not null_ok: overall='INCONCLUSIVE'
    else: overall='FAIL'
    blind_verdict=dict(version='0.3.0',hypothesis='Trefoil self-confinement, if present, may be a dynamical balance among breathing, torsion and Kelvin-like modes rather than a static cross-lobe repulsion; v0.3 tests coupled-mode causality, phase locking, relative-periodic recurrence and nonlinear Floquet stability without changing the v0.1 critical gates.',overall=overall,blind_scores=scores,circle_nulls=nulls,physical_scales={b:physical_scales(cfg,results[b]['core_radius_norm']) for b in results},runtime_s=time.time()-t0)
    write_json(pre/'blind_verdict.json',blind_verdict)
    mapping={blind[i]:manifest[i] for i in range(len(inputs))};write_json(out/'unblind_manifest.json',mapping)
    unblinded={mapping[b]['source']:scores[b] for b in scores}; final=dict(**blind_verdict,unblinded_scores=unblinded,blind_to_source={b:mapping[b]['source'] for b in mapping});write_json(out/'final_verdict.json',final)
    return final,results,mapping
